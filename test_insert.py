#!/usr/bin/env python3
"""
Script para probar la inserción de datos y creación de tabla SQL
"""

import requests
import json

def test_create_table():
    """Prueba la creación de una tabla SQL real desde Excel"""
    
    # URL base
    base_url = "http://localhost:8000"
    
    # 1. Primero hacer preview del archivo
    print("📊 1. Haciendo preview del archivo Excel...")
    
    with open("productos_prueba.xlsx", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/api/v1/upload/preview", files=files)
    
    if response.status_code != 200:
        print(f"❌ Error en preview: {response.status_code}")
        print(response.text)
        return
    
    preview_data = response.json()
    print(f"✅ Preview exitoso: {len(preview_data['data']['rows'])} filas")
    
    # 2. Crear tabla SQL real
    print("\n🏗️ 2. Creando tabla SQL real...")
    
    # Preparar datos para inserción
    insert_data = {
        "table": "create_new",
        "mapping": {
            "Nombre": "Nombre",
            "Categoría": "Categoría", 
            "Precio": "Precio",
            "Stock": "Stock",
            "Fecha_Ingreso": "Fecha_Ingreso",
            "Activo": "Activo"
        },
        "data": preview_data['data']['rows'],
        "create_new_table": True,
        "new_table_info": {
            "table_name": "productos_test",
            "display_name": "Productos de Prueba",
            "description": "Tabla creada desde Excel para pruebas",
            "columns": [
                {
                    "name": "Nombre",
                    "display_name": "Nombre del Producto",
                    "data_type": "TEXT",
                    "required": True
                },
                {
                    "name": "Categoría",
                    "display_name": "Categoría del Producto", 
                    "data_type": "TEXT",
                    "required": False
                },
                {
                    "name": "Precio",
                    "display_name": "Precio del Producto",
                    "data_type": "REAL",
                    "required": True
                },
                {
                    "name": "Stock",
                    "display_name": "Stock Disponible",
                    "data_type": "INTEGER",
                    "required": False
                },
                {
                    "name": "Fecha_Ingreso",
                    "display_name": "Fecha de Ingreso",
                    "data_type": "DATE",
                    "required": False
                },
                {
                    "name": "Activo",
                    "display_name": "Producto Activo",
                    "data_type": "BOOLEAN",
                    "required": False
                }
            ]
        }
    }
    
    # Enviar petición para crear tabla e insertar datos
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{base_url}/api/v1/upload/insert",
        json=insert_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Error en inserción: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"✅ Tabla creada exitosamente!")
    print(f"📊 Registros insertados: {result['inserted_count']}")
    print(f"⚠️ Registros omitidos: {result['skipped_count']}")
    print(f"📋 Total procesados: {result['total_count']}")
    
    if result['table_created']:
        print(f"🏗️ Nueva tabla: {result['new_table_name']}")
    
    if result['errors']:
        print(f"❌ Errores: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - {error}")
    
    # 3. Verificar que la tabla se creó
    print("\n🔍 3. Verificando tablas disponibles...")
    
    response = requests.get(f"{base_url}/api/v1/upload/tables")
    if response.status_code == 200:
        tables = response.json()
        print(f"✅ Tablas disponibles: {list(tables['tables'].keys())}")
        
        if 'productos_test' in tables['tables']:
            table_info = tables['tables']['productos_test']
            print(f"📋 Columnas de productos_test: {table_info['columns']}")
    
    print("\n🎉 ¡Prueba completada exitosamente!")

if __name__ == "__main__":
    test_create_table() 