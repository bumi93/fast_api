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