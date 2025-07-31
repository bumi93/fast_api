# app/db/init_static_data.py
"""
Script para inicializar la base de datos con datos estáticos de ejemplo

Este script crea las tablas y las llena con datos de referencia que no cambian frecuentemente.
Se ejecuta una sola vez para configurar la base de datos inicial.

Autor: Tu Nombre
Versión: 1.0.0
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.models import Base, UserDB, Feriado, DiccionarioCatalogoEmpresa, DynamicTable, DynamicTableData
from app.db.session import DATABASE_URL

def create_tables():
    """Crea todas las tablas en la base de datos"""
    try:
        # Crear engine de base de datos
        engine = create_engine(DATABASE_URL)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas exitosamente")
        return engine
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {str(e)}")
        return None

def insert_static_data(engine):
    """Inserta datos estáticos de ejemplo en las tablas"""
    try:
        # Crear sesión de base de datos
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("📝 Insertando datos estáticos...")
        
        # 1. Insertar feriados de países latinoamericanos
        feriados = [
            # Chile
            Feriado(pais="Chile", feriado="Año Nuevo", fecha=date(2024, 1, 1)),
            Feriado(pais="Chile", feriado="Viernes Santo", fecha=date(2024, 3, 29)),
            Feriado(pais="Chile", feriado="Sábado Santo", fecha=date(2024, 3, 30)),
            Feriado(pais="Chile", feriado="Día del Trabajo", fecha=date(2024, 5, 1)),
            Feriado(pais="Chile", feriado="Glorias Navales", fecha=date(2024, 5, 21)),
            Feriado(pais="Chile", feriado="San Pedro y San Pablo", fecha=date(2024, 6, 29)),
            Feriado(pais="Chile", feriado="Día de la Virgen del Carmen", fecha=date(2024, 7, 16)),
            Feriado(pais="Chile", feriado="Asunción de la Virgen", fecha=date(2024, 8, 15)),
            Feriado(pais="Chile", feriado="Independencia Nacional", fecha=date(2024, 9, 18)),
            Feriado(pais="Chile", feriado="Glorias del Ejército", fecha=date(2024, 9, 19)),
            Feriado(pais="Chile", feriado="Encuentro de Dos Mundos", fecha=date(2024, 10, 12)),
            Feriado(pais="Chile", feriado="Día de las Iglesias Evangélicas", fecha=date(2024, 10, 31)),
            Feriado(pais="Chile", feriado="Inmaculada Concepción", fecha=date(2024, 12, 8)),
            Feriado(pais="Chile", feriado="Navidad", fecha=date(2024, 12, 25)),
            
            # Perú
            Feriado(pais="Perú", feriado="Año Nuevo", fecha=date(2024, 1, 1)),
            Feriado(pais="Perú", feriado="Jueves Santo", fecha=date(2024, 3, 28)),
            Feriado(pais="Perú", feriado="Viernes Santo", fecha=date(2024, 3, 29)),
            Feriado(pais="Perú", feriado="Día del Trabajo", fecha=date(2024, 5, 1)),
            Feriado(pais="Perú", feriado="San Pedro y San Pablo", fecha=date(2024, 6, 29)),
            Feriado(pais="Perú", feriado="Independencia del Perú", fecha=date(2024, 7, 28)),
            Feriado(pais="Perú", feriado="Batalla de Junín", fecha=date(2024, 8, 6)),
            Feriado(pais="Perú", feriado="Santa Rosa de Lima", fecha=date(2024, 8, 30)),
            Feriado(pais="Perú", feriado="Combate de Angamos", fecha=date(2024, 10, 8)),
            Feriado(pais="Perú", feriado="Todos los Santos", fecha=date(2024, 11, 1)),
            Feriado(pais="Perú", feriado="Inmaculada Concepción", fecha=date(2024, 12, 8)),
            Feriado(pais="Perú", feriado="Batalla de Ayacucho", fecha=date(2024, 12, 9)),
            Feriado(pais="Perú", feriado="Navidad", fecha=date(2024, 12, 25)),
            
            # Colombia
            Feriado(pais="Colombia", feriado="Año Nuevo", fecha=date(2024, 1, 1)),
            Feriado(pais="Colombia", feriado="Reyes Magos", fecha=date(2024, 1, 8)),
            Feriado(pais="Colombia", feriado="San José", fecha=date(2024, 3, 25)),
            Feriado(pais="Colombia", feriado="Jueves Santo", fecha=date(2024, 3, 28)),
            Feriado(pais="Colombia", feriado="Viernes Santo", fecha=date(2024, 3, 29)),
            Feriado(pais="Colombia", feriado="Día del Trabajo", fecha=date(2024, 5, 1)),
            Feriado(pais="Colombia", feriado="Ascensión del Señor", fecha=date(2024, 5, 13)),
            Feriado(pais="Colombia", feriado="Corpus Christi", fecha=date(2024, 6, 3)),
            Feriado(pais="Colombia", feriado="Sagrado Corazón", fecha=date(2024, 6, 10)),
            Feriado(pais="Colombia", feriado="San Pedro y San Pablo", fecha=date(2024, 7, 1)),
            Feriado(pais="Colombia", feriado="Independencia de Colombia", fecha=date(2024, 7, 20)),
            Feriado(pais="Colombia", feriado="Batalla de Boyacá", fecha=date(2024, 8, 7)),
            Feriado(pais="Colombia", feriado="Asunción de la Virgen", fecha=date(2024, 8, 19)),
            Feriado(pais="Colombia", feriado="Día de la Raza", fecha=date(2024, 10, 14)),
            Feriado(pais="Colombia", feriado="Todos los Santos", fecha=date(2024, 11, 4)),
            Feriado(pais="Colombia", feriado="Independencia de Cartagena", fecha=date(2024, 11, 11)),
            Feriado(pais="Colombia", feriado="Inmaculada Concepción", fecha=date(2024, 12, 8)),
            Feriado(pais="Colombia", feriado="Navidad", fecha=date(2024, 12, 25)),
            
            # México
            Feriado(pais="México", feriado="Año Nuevo", fecha=date(2024, 1, 1)),
            Feriado(pais="México", feriado="Día de la Constitución", fecha=date(2024, 2, 5)),
            Feriado(pais="México", feriado="Natalicio de Benito Juárez", fecha=date(2024, 3, 18)),
            Feriado(pais="México", feriado="Jueves Santo", fecha=date(2024, 3, 28)),
            Feriado(pais="México", feriado="Viernes Santo", fecha=date(2024, 3, 29)),
            Feriado(pais="México", feriado="Día del Trabajo", fecha=date(2024, 5, 1)),
            Feriado(pais="México", feriado="Batalla de Puebla", fecha=date(2024, 5, 5)),
            Feriado(pais="México", feriado="Independencia de México", fecha=date(2024, 9, 16)),
            Feriado(pais="México", feriado="Revolución Mexicana", fecha=date(2024, 11, 18)),
            Feriado(pais="México", feriado="Navidad", fecha=date(2024, 12, 25)),
            
            # Argentina
            Feriado(pais="Argentina", feriado="Año Nuevo", fecha=date(2024, 1, 1)),
            Feriado(pais="Argentina", feriado="Carnaval", fecha=date(2024, 2, 12)),
            Feriado(pais="Argentina", feriado="Carnaval", fecha=date(2024, 2, 13)),
            Feriado(pais="Argentina", feriado="Día de la Memoria", fecha=date(2024, 3, 24)),
            Feriado(pais="Argentina", feriado="Viernes Santo", fecha=date(2024, 3, 29)),
            Feriado(pais="Argentina", feriado="Día del Veterano", fecha=date(2024, 4, 2)),
            Feriado(pais="Argentina", feriado="Día del Trabajo", fecha=date(2024, 5, 1)),
            Feriado(pais="Argentina", feriado="Revolución de Mayo", fecha=date(2024, 5, 25)),
            Feriado(pais="Argentina", feriado="Día de la Bandera", fecha=date(2024, 6, 20)),
            Feriado(pais="Argentina", feriado="Independencia Argentina", fecha=date(2024, 7, 9)),
            Feriado(pais="Argentina", feriado="Muerte del General San Martín", fecha=date(2024, 8, 17)),
            Feriado(pais="Argentina", feriado="Día del Respeto a la Diversidad", fecha=date(2024, 10, 14)),
            Feriado(pais="Argentina", feriado="Día de la Soberanía Nacional", fecha=date(2024, 11, 20)),
            Feriado(pais="Argentina", feriado="Inmaculada Concepción", fecha=date(2024, 12, 8)),
            Feriado(pais="Argentina", feriado="Navidad", fecha=date(2024, 12, 25)),
        ]
        
        for feriado in feriados:
            db.add(feriado)
        print("✅ Feriados insertados")
        
        # 2. Insertar diccionario catálogo empresa
        catalogo_empresa = [
            DiccionarioCatalogoEmpresa(empresa="LATAM Airlines", valor="Aerolínea principal de Chile y Latinoamérica"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Airlines", valor="Código IATA: LA"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Airlines", valor="Hub principal: Santiago de Chile"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Airlines", valor="Fundada: 1929"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Airlines", valor="Sede: Santiago, Chile"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Cargo", valor="División de carga de LATAM Airlines"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Cargo", valor="Especializada en transporte de carga aérea"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Cargo", valor="Cobertura: América Latina y el mundo"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Pass", valor="Programa de fidelización de LATAM"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Pass", valor="Acumulación de millas por vuelos"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Pass", valor="Canje de millas por premios"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Vacations", valor="División de turismo y vacaciones"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Vacations", valor="Paquetes turísticos completos"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Vacations", valor="Hoteles y tours incluidos"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Express", valor="Servicio de envío de documentos"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Express", valor="Entrega rápida en 24-48 horas"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Express", valor="Cobertura nacional e internacional"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM MRO", valor="Mantenimiento, Reparación y Operaciones"),
            DiccionarioCatalogoEmpresa(empresa="LATAM MRO", valor="Servicios de mantenimiento aeronáutico"),
            DiccionarioCatalogoEmpresa(empresa="LATAM MRO", valor="Hangares en Santiago y Lima"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Training", valor="Centro de entrenamiento de pilotos"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Training", valor="Simuladores de vuelo"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Training", valor="Certificaciones aeronáuticas"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Technology", valor="División de tecnología e innovación"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Technology", valor="Desarrollo de aplicaciones móviles"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Technology", valor="Sistemas de reservas y gestión"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Finance", valor="División financiera del grupo"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Finance", valor="Gestión de inversiones y finanzas"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Finance", valor="Relaciones con bancos e inversores"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM HR", valor="Recursos Humanos del grupo"),
            DiccionarioCatalogoEmpresa(empresa="LATAM HR", valor="Gestión de personal y talento"),
            DiccionarioCatalogoEmpresa(empresa="LATAM HR", valor="Desarrollo organizacional"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Legal", valor="Asesoría legal corporativa"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Legal", valor="Cumplimiento regulatorio"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Legal", valor="Contratos y acuerdos comerciales"),
            
            DiccionarioCatalogoEmpresa(empresa="LATAM Procurement", valor="Compras y abastecimiento"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Procurement", valor="Gestión de proveedores"),
            DiccionarioCatalogoEmpresa(empresa="LATAM Procurement", valor="Contrataciones y licitaciones"),
        ]
        
        for catalogo in catalogo_empresa:
            db.add(catalogo)
        print("✅ Diccionario Catálogo Empresa insertado")
        
        # Commit de todos los cambios
        db.commit()
        print("✅ Todos los datos insertados exitosamente")
        
        # Cerrar sesión
        db.close()
        
    except Exception as e:
        print(f"❌ Error al insertar datos: {str(e)}")
        db.rollback()
        db.close()

def main():
    """Función principal para inicializar la base de datos"""
    print("🚀 Iniciando configuración de base de datos...")
    
    # Crear tablas
    engine = create_tables()
    if not engine:
        return
    
    # Insertar datos estáticos
    insert_static_data(engine)
    
    print("🎉 Configuración de base de datos completada exitosamente!")

if __name__ == "__main__":
    main() 