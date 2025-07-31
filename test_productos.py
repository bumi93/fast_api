#!/usr/bin/env python3
"""
Script para crear archivo Excel de prueba para el sistema de migración
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def crear_archivo_excel_prueba():
    """Crea un archivo Excel con datos de productos para probar el sistema"""
    
    # Datos de ejemplo
    productos = [
        "Laptop HP Pavilion",
        "Mouse Logitech G502",
        "Teclado Mecánico Corsair",
        "Monitor Samsung 24\"",
        "Auriculares Sony WH-1000XM4",
        "Webcam Logitech C920",
        "Disco Duro Seagate 1TB",
        "Memoria RAM Kingston 8GB",
        "Tarjeta Gráfica NVIDIA RTX 3060",
        "Fuente de Poder EVGA 650W"
    ]
    
    categorias = ["Electrónicos", "Periféricos", "Componentes", "Audio", "Almacenamiento"]
    
    # Generar datos aleatorios
    datos = []
    for i in range(50):  # 50 productos
        producto = random.choice(productos)
        categoria = random.choice(categorias)
        precio = round(random.uniform(50, 2000), 2)
        stock = random.randint(0, 100)
        fecha = datetime.now() - timedelta(days=random.randint(0, 365))
        
        datos.append({
            "Nombre": producto,
            "Categoría": categoria,
            "Precio": precio,
            "Stock": stock,
            "Fecha_Ingreso": fecha.strftime("%Y-%m-%d"),
            "Activo": random.choice([True, False])
        })
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    
    # Guardar como Excel
    nombre_archivo = "productos_prueba.xlsx"
    df.to_excel(nombre_archivo, index=False)
    
    print(f"✅ Archivo Excel creado: {nombre_archivo}")
    print(f"📊 Datos generados: {len(df)} productos")
    print(f"📋 Columnas: {list(df.columns)}")
    print("\n📄 Primera fila:")
    print(df.head(1).to_string(index=False))
    
    return nombre_archivo

if __name__ == "__main__":
    crear_archivo_excel_prueba() 