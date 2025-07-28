# app/scraping/ariba_scraper.py

import os
import time
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Dict, Any, Tuple
from app.core.config import DOWNLOAD_DIR


def setup_driver(headless: bool = True, download_path: str = None) -> webdriver.Chrome:
    """
    Configura y retorna una instancia de Chrome WebDriver
    
    Args:
        headless: Si es True, ejecuta Chrome en modo headless
        download_path: Ruta para las descargas de Chrome
    """
    if download_path is None:
        download_path = DOWNLOAD_DIR
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Eliminar la opción detach que causa problemas con múltiples ventanas
    # chrome_options.add_experimental_option("detach", True)
    
    # Agregar opciones para evitar múltiples ventanas
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    if download_path:
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_path
        })
    
    return webdriver.Chrome(options=chrome_options)

def login_ariba(email: str, password: str, headless: bool = False, download_path: str = None) -> Tuple[webdriver.Chrome, bool, str]:
    """
    Inicia sesión en Ariba usando las credenciales proporcionadas
    
    Args:
        email: Email para el login
        password: Contraseña para el login
        headless: Si es True, ejecuta Chrome en modo headless
        download_path: Ruta opcional para las descargas
        
    Returns:
        Tuple con (driver, success, message)
    """
    try:
        driver = setup_driver(headless=headless, download_path=download_path)
        
        # Abre Ariba
        driver.get("https://s1.ariba.com/Sourcing/Main/aw?awh=r&awssk=.qzgIa5z&realm=latam&dard=1#b0")
        
        # Configurar espera explícita
        wait = WebDriverWait(driver, 15)
        
        # Login con email
        usuario = wait.until(EC.presence_of_element_located((
            By.XPATH, "/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div[1]/div[3]/div/div/div/div[2]/div[2]/div/input[1]"
        )))
        usuario.send_keys(email)
        usuario.send_keys(Keys.RETURN)
        
        time.sleep(4)
        
        # Login con password
        clave = wait.until(EC.presence_of_element_located((
            By.XPATH, "/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div/div[3]/div/div[2]/div/div[3]/div/div[2]/input"
        )))
        clave.send_keys(password)
        clave.send_keys(Keys.RETURN)
        
        time.sleep(5)
        
        print("Esperando autenticación 2FA...")
        input("Por favor, completa la autenticación 2FA en el dispositivo y luego presiona Enter aquí...")
        
        # Verificar login exitoso
        wait = WebDriverWait(driver, 300)
        validador = wait.until(EC.presence_of_element_located((
            By.XPATH, "/html/body/div[5]/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[4]/td/table/tbody/tr/td[1]/div/div/ul/span[1]/li/span/a"
        ))).get_attribute('outerText')
        
        if validador == "INICIO":
            return driver, True, "Ariba ha sido abierto exitosamente"
        else:
            driver.quit()
            return None, False, "Error: No se pudo verificar el login en Ariba"
            
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return None, False, f"Error: {str(e)}"

def scrape_page(url, selectors, wait_time=10, headless=True):
    """
    Realiza scraping de una página usando Selenium y selectores CSS.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    data = {}
    for key, selector in selectors.items():
        try:
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            data[key] = element.text
        except Exception:
            data[key] = None
    driver.quit()
    return data 

class AribaCredentials:
    """Clase para manejar las credenciales de Ariba"""
    CREDENTIALS = {
        "driver": {
            "email": "franciscoalvarez.aquanima@latam.com",
            "password": "Aquanima_123"
        },
        "driver_m": {
            "email": "4637043@outsourcing-account.com",
            "password": "Aquanima.2025.2"
        }
    }

    @classmethod
    def get_credentials(cls, driver_name: str) -> Optional[dict]:
        return cls.CREDENTIALS.get(driver_name)

def descarga_db(driver, path):
    """
    Descarga archivos CSV desde Ariba usando el driver proporcionado
    Solo descarga archivos que no existen o que no son de hoy
    
    Args:
        driver: Instancia de WebDriver activa y logueada en Ariba
        path: Ruta base donde se guardarán los archivos
        
    Returns:
        Tuple con (success, message)
    """
    try:
        from datetime import datetime, date
        
        folder_path = path
        today = date.today()
        archivos_descargados = 0
        archivos_omitidos = 0

        # Crear la carpeta si no existe
        os.makedirs(folder_path, exist_ok=True)
        
        # Función para verificar si un archivo es de hoy
        def archivo_es_de_hoy(file_path):
            if not os.path.exists(file_path):
                return False
            try:
                # Obtener la fecha de modificación del archivo
                timestamp = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(timestamp).date()
                return file_date == today
            except Exception:
                return False
        
        #-------------------------------------------------------------------------------------
        lista_csv = ["PR's", "CATALOG", "LEGAL", "IVA", "Categoría PR", "Categoria PR Lega" ,"Fecha_reque", "Pedidos Lata", "Sourcing DB", "DB Gerencia Compras", "Materiales", "PXC", "AQN_OTIF", "Reporte Proveedores v2", "especiales 2024 - Francisco", "SAP_MAT_SER", "Moneda y Pedido"]

        # lista_csv = ["especiales 2024 - Francisco"]

         #Antes era 12
        
        lista_rutas = ["Backlog COMPRAS - LATAM - PR's.csv","Backlog COMPRAS - LATAM - CATALOG.csv", "Backlog BPO PROCESO LEGAL.csv", "BACKPG PR - IVA.csv", "Categoría PR Compras.csv" , "Categoria PR Legal.csv", "Fecha_requerida.csv", "Pedidos Latam.csv", "Sourcing DB.csv", "DB Gerencia Compras.csv" , "Materiales LATAM.csv", "OTIF - Material - PXC.csv", "AQN_OTIF_OT.csv", "Reporte Proveedores v2.csv", "PR especiales 2024 - Francisco.csv", "SAP_MAT_SER.csv", "Moneda y Pedidos.csv"]

        # lista_rutas = ["PR especiales 2024 - Francisco.csv"]
 
        i = 0
        
        for nombre in lista_csv:
            path_archivos = folder_path + "\\" + lista_rutas[i]
            
            # Verificar si el archivo ya existe y es de hoy
            if archivo_es_de_hoy(path_archivos):
                print(f'--> Archivo {nombre} ya existe y es de hoy. Omitiendo descarga.')
                archivos_omitidos += 1
                i += 1
                continue
            
            print('--> Se descargará el archivo: ', path_archivos)
            archivos_descargados += 1

            time.sleep(10)

            validador = True
            
            while validador:
            #Ingresar a área Personal
                try:
                    wait = WebDriverWait(driver, 10)
                    try:
                        gestionar = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[4]/td/table/tbody/tr/td[3]/div/table/tbody/tr/td[2]/a")))
                    except:
                        try:
                            gestionar = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='_s2d3v']")))
                        except:
                            gestionar = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Gestionar")))
                            
                    gestionar.click()
                    time.sleep(3)
                    areaperso = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'de trabajo personal')))
                    areaperso.click()

                    time.sleep(5)

                    #Descargar archivo
                    backlog = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, nombre)))
                    backlog.click()
                    time.sleep(3)
                    link_archivo = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/form/div[4]/div/div[3]/a[2]")))
                    link_archivo.click()

                    while not os.path.isfile(path_archivos):
                        time.sleep(1)

                    time.sleep(2)
                        
                    try:
                        wait = WebDriverWait(driver, 5)
                        volver = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/div[1]/a")))
                        volver.click()
                    except:
                        volver = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/form/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[2]/div/div/div/div/div/div[1]/table/tbody/tr/td[3]/table/tbody/tr/td/table/tbody/tr/td/button")))
                        volver.click()

                        time.sleep(1)

                        inicio = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/form/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/div[1]/a")))
                        inicio.click()
                        #-------------------------------------
                    if os.path.exists(path_archivos):
                        print("--> Descarga archivo " + nombre + " LATAM correcto.")
                        validador = False
                        i += 1
                    else:
                        print("--> El archivo no existe.")
                       
            #Validados que este descargado
                except:
                    time.sleep(3)
                    try:
                        boton_completado = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/form/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[2]/div/div/div/div/div/div[5]/table/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/button")))
                        validador = boton_completado.get_attribute("innerText")

                        if validador == "Completado":
                            boton_completado.click()
                        else:
                            pass
                    except:
                        pass

                    time.sleep(1)
                    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/form/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/div[2]/div/a"))).click()
                    time.sleep(1)

        # Mensaje final con estadísticas
        mensaje = f"--> Proceso completado. Archivos descargados: {archivos_descargados}, Archivos omitidos (ya existían de hoy): {archivos_omitidos}"
        return True, mensaje
        
    except Exception as e:
        return False, f"Error en descarga_db: {str(e)}" 