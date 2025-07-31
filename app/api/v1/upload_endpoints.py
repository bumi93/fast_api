# app/api/v1/upload_endpoints.py
"""
Endpoints para migración de Excel a tablas SQL reales

Este módulo proporciona endpoints para:
- Subir archivos Excel y obtener preview
- Crear tablas SQL reales basadas en Excel
- Insertar datos de Excel en tablas SQL
- Listar tablas existentes
"""

import pandas as pd
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import Dict, List, Any, Optional
import tempfile
import os
from datetime import datetime

# Importar nuestros módulos
from app.db.session import SessionLocal
from app.crud.excel_migration import (
    create_table_from_excel_data,
    insert_data_to_table,
    get_existing_tables,
    get_table_columns,
    validate_table_name
)
from app.schemas.excel_migration import (
    DataInsertRequest,
    DataInsertResponse,
    TablesListResponse,
    TableInfo,
    PreviewResponse,
    PreviewData,
    CreateTableRequest
)
from app.core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Crear router
router = APIRouter(prefix="/upload", tags=["Excel Migration"])

# Dependencia para obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear engine de SQLAlchemy para operaciones directas
def get_engine():
    return create_engine(settings.DATABASE_URL)

# ============================================================================
# Endpoints de Interfaz Web
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Página principal de upload de Excel"""
    return templates.TemplateResponse("upload.html", {"request": request})

# ============================================================================
# Endpoints de API
# ============================================================================

@router.post("/preview")
async def preview_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> PreviewResponse:
    """
    Sube un archivo Excel y devuelve una previsualización de sus datos
    """
    try:
        # Validar tipo de archivo
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=400, 
                detail="Solo se permiten archivos Excel (.xlsx, .xls) o CSV (.csv)"
            )
        
        # Validar tamaño (máximo 10MB)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="El archivo no puede ser mayor a 10MB"
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Leer archivo con pandas
            if file.filename.lower().endswith('.csv'):
                df = pd.read_csv(tmp_file_path)
            else:
                df = pd.read_excel(tmp_file_path)
            
            # Limpiar datos
            df = df.dropna(how='all')  # Eliminar filas completamente vacías
            
            # Preparar datos de preview
            preview_data = PreviewData(
                columns=df.columns.tolist(),
                rows=df.head(10).to_dict('records'),
                total_rows=len(df),
                file_info={
                    "filename": file.filename,
                    "size": file.size,
                    "columns_count": len(df.columns),
                    "rows_count": len(df)
                }
            )
            
            return PreviewResponse(
                success=True,
                data=preview_data
            )
            
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        return PreviewResponse(
            success=False,
            message=f"Error procesando archivo: {str(e)}"
        )

@router.get("/tables")
async def get_tables(db: Session = Depends(get_db)) -> TablesListResponse:
    """
    Obtiene lista de tablas disponibles en la base de datos
    """
    try:
        engine = get_engine()
        existing_tables = get_existing_tables(engine)
        
        tables_info = {}
        
        # Agregar tablas estáticas predefinidas
        static_tables = {
            'feriados': {
                'name': 'Feriados',
                'description': 'Tabla de feriados por país',
                'columns': ['pais', 'feriado', 'fecha']
            },
            'diccionario_catalogo_empresa': {
                'name': 'Diccionario Catálogo Empresa',
                'description': 'Tabla de catálogo de empresas',
                'columns': ['empresa', 'valor']
            }
        }
        
        for table_name, info in static_tables.items():
            if table_name in existing_tables:
                tables_info[table_name] = TableInfo(
                    name=info['name'],
                    display_name=info['name'],
                    description=info['description'],
                    columns=info['columns']
                )
        
        # Agregar tablas dinámicas creadas por el usuario
        for table_name in existing_tables:
            if table_name not in static_tables:
                columns = get_table_columns(engine, table_name)
                tables_info[table_name] = TableInfo(
                    name=table_name,
                    display_name=table_name.replace('_', ' ').title(),
                    description=f"Tabla creada desde Excel: {table_name}",
                    columns=columns
                )
        
        return TablesListResponse(
            success=True,
            tables=tables_info
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo tablas: {str(e)}")
        return TablesListResponse(
            success=False,
            tables={},
            message=f"Error obteniendo tablas: {str(e)}"
        )

@router.post("/insert")
async def insert_excel_data(
    request: DataInsertRequest,
    db: Session = Depends(get_db)
) -> DataInsertResponse:
    """
    Inserta datos de Excel en una tabla SQL (existente o nueva)
    """
    try:
        engine = get_engine()
        
        # Si se debe crear una nueva tabla
        if request.create_new_table and request.new_table_info:
            table_info = request.new_table_info
            
            # Validar nombre de tabla
            if not validate_table_name(table_info.table_name):
                raise HTTPException(
                    status_code=400,
                    detail="Nombre de tabla inválido"
                )
            
            # Verificar si la tabla ya existe
            existing_tables = get_existing_tables(engine)
            if table_info.table_name in existing_tables:
                raise HTTPException(
                    status_code=400,
                    detail=f"La tabla '{table_info.table_name}' ya existe"
                )
            
            # Crear DataFrame temporal para inferir tipos
            df_temp = pd.DataFrame(request.data)
            
            # Crear tabla
            success = create_table_from_excel_data(
                engine=engine,
                table_name=table_info.table_name,
                df=df_temp
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Error creando la tabla"
                )
            
            # Insertar datos en la nueva tabla
            inserted, skipped, errors = insert_data_to_table(
                engine=engine,
                table_name=table_info.table_name,
                df=df_temp,
                column_mapping=request.column_mapping
            )
            
            return DataInsertResponse(
                success=True,
                message=f"Tabla '{table_info.table_name}' creada y datos insertados",
                inserted_count=inserted,
                skipped_count=skipped,
                total_count=len(request.data),
                errors=errors,
                table_created=True,
                new_table_name=table_info.table_name
            )
        
        else:
            # Insertar en tabla existente
            if not request.table_name:
                raise HTTPException(
                    status_code=400,
                    detail="Debe especificar una tabla destino"
                )
            
            # Verificar que la tabla existe
            existing_tables = get_existing_tables(engine)
            if request.table_name not in existing_tables:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tabla '{request.table_name}' no encontrada"
                )
            
            # Crear DataFrame y insertar datos
            df = pd.DataFrame(request.data)
            inserted, skipped, errors = insert_data_to_table(
                engine=engine,
                table_name=request.table_name,
                df=df,
                column_mapping=request.column_mapping
            )
            
            return DataInsertResponse(
                success=True,
                message=f"Datos insertados en tabla '{request.table_name}'",
                inserted_count=inserted,
                skipped_count=skipped,
                total_count=len(request.data),
                errors=errors,
                table_created=False
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error insertando datos: {str(e)}")
        return DataInsertResponse(
            success=False,
            message=f"Error insertando datos: {str(e)}",
            inserted_count=0,
            skipped_count=len(request.data),
            total_count=len(request.data),
            errors=[str(e)]
        )

@router.post("/create-table")
async def create_table_from_excel(
    file: UploadFile = File(...),
    table_name: str = Form(...),
    display_name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva tabla SQL basada en un archivo Excel
    """
    try:
        # Validar nombre de tabla
        if not validate_table_name(table_name):
            raise HTTPException(
                status_code=400,
                detail="Nombre de tabla inválido"
            )
        
        # Verificar que la tabla no existe
        engine = get_engine()
        existing_tables = get_existing_tables(engine)
        if table_name in existing_tables:
            raise HTTPException(
                status_code=400,
                detail=f"La tabla '{table_name}' ya existe"
            )
        
        # Procesar archivo Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Leer archivo
            if file.filename.lower().endswith('.csv'):
                df = pd.read_csv(tmp_file_path)
            else:
                df = pd.read_excel(tmp_file_path)
            
            # Crear tabla
            success = create_table_from_excel_data(
                engine=engine,
                table_name=table_name,
                df=df
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Tabla '{table_name}' creada exitosamente",
                    "table_name": table_name,
                    "columns": df.columns.tolist()
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Error creando la tabla"
                )
                
        finally:
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tabla: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creando tabla: {str(e)}"
        ) 