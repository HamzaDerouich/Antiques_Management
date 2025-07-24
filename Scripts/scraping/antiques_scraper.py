# Script principal para scraping de antigüedades
# Aquí va el código principal del scraper.
# -*- coding: utf-8 -*-
"""
Antiques.py
------------
Main scraper to extract antique item data from the 4AM admin panel.

FUNCTIONALITY:
- Performs automatic login to the admin site.
- Navigates through all item pages.
- For each item:
    - Extracts ID, name, category, number of images, price, featured, status, updated date.
    - Extracts all image links (forcing https).
    - Accesses the edit page to extract and summarize the HTML description (DescriptionSummary).
- Saves results in CSV and JSON in the 'output' folder (created if it does not exist).
- Makes partial backups every 200 items.

REQUIREMENTS:
- Selenium, beautifulsoup4, re, csv
- ChromeDriver installed and path configured

OUTPUT:
- output/items_all.csv
- output/items_all.json
- output/items_backup_X.json (every 200 items)

Author: hamza
Last modified: 2025-05-30
"""
import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re
import csv
import os

# CONFIGURATION
LOGIN_URL = "https://4am.ie/Logon.aspx?admin&ReturnUrl=%2fAdmin%2fItems.aspx"  # Updated login URL
ITEMS_URL = "https://4am.ie/Admin/Items.aspx"
USERNAME = "martinfennelly@gmail.com"
PASSWORD = "martinfennelly"  # <--- PUT YOUR PASSWORD

# Selectors for login fields (adjust according to real HTML)
USERNAME_FIELD = "ctl00_ContentPlaceHolderBody_username"  # user field id
PASSWORD_FIELD = "ctl00_ContentPlaceHolderBody_password"  # password field id
LOGIN_BUTTON = "ctl00_ContentPlaceHolderBody_Button1"     # login button id

# Constantes de navegación
START_PAGE = 31  # Página donde quieres empezar
END_PAGE = 43    # Última página a procesar
MAX_RETRIES = 5  # Número máximo de intentos para navegación
WAIT_BETWEEN_PAGES = 4  # Aumentado a 4 segundos
WAIT_BETWEEN_ROWS = 1  # Espera entre filas
WAIT_AFTER_REFRESH = 3  # Espera después de recargar la página

# Create output folder if it does not exist
os.makedirs('output', exist_ok=True)

def load_existing_data():
    """Carga datos existentes del archivo JSON más reciente"""
    try:
        # Buscar el archivo de backup más reciente
        backup_files = [f for f in os.listdir('output') if f.startswith('items_backup_') and f.endswith('.json')]
        if not backup_files:
            return [], set()
        
        # Ordenar por fecha de modificación del archivo
        latest_backup = max(backup_files, key=lambda x: os.path.getmtime(os.path.join('output', x)))
        backup_path = os.path.join('output', latest_backup)
        
        print(f"📂 Cargando datos existentes desde {backup_path}")
        with open(backup_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # Crear conjunto de IDs procesados
        processed_ids = {item['ID'] for item in existing_data}
        print(f"✅ Cargados {len(existing_data)} items previos")
        return existing_data, processed_ids
        
    except Exception as e:
        print(f"⚠️ Error cargando datos existentes: {e}")
        return [], set()

# Initialize browser con opciones mejoradas
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(service=service, options=options)

# Cargar datos existentes
all_data, seen_ids = load_existing_data()
wait = WebDriverWait(driver, 20)

# 1. Login con verificación
print("\n=== INICIANDO SESIÓN ===")
try:
    driver.get(LOGIN_URL)
    print("✅ Página de login cargada")
    
    # Esperar y verificar campos de login
    wait.until(EC.presence_of_element_located((By.ID, USERNAME_FIELD)))
    wait.until(EC.presence_of_element_located((By.ID, PASSWORD_FIELD)))
    wait.until(EC.presence_of_element_located((By.ID, LOGIN_BUTTON)))
    print("✅ Campos de login detectados")
    
    # Ingresar credenciales
    driver.find_element(By.ID, USERNAME_FIELD).send_keys(USERNAME)
    driver.find_element(By.ID, PASSWORD_FIELD).send_keys(PASSWORD)
    print("✅ Credenciales ingresadas")
    
    # Click en login y esperar redirección
    driver.find_element(By.ID, LOGIN_BUTTON).click()
    wait.until(EC.url_contains("Admin"))
    print("✅ Login exitoso")
    
    # 2. Ir a la página de items con verificación
    print("\n=== ACCEDIENDO A ITEMS ===")
    driver.get(ITEMS_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    print("✅ Página de items cargada")
    
    # Verificar que hay datos en la tabla
    rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
    if len(rows) > 1:
        print(f"✅ Tabla cargada con {len(rows)-1} items")
    else:
        raise Exception("La tabla no contiene datos")
        
except Exception as e:
    print(f"\n❌ Error en la inicialización: {e}")
    driver.quit()
    exit(1)

# Pequeña pausa para asegurar que todo está cargado
time.sleep(5)  # Espera 5 segundos antes de comenzar

def get_item_images_from_td(td):
    images = []
    main_window = driver.current_window_handle
    try:
        link = td.find_element(By.TAG_NAME, 'a')
        img_url = link.get_attribute('href')
        driver.execute_script("window.open(arguments[0]);", img_url)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(3)  # Aumentado de 1.5 a 3 segundos
        # Find all <li> inside the image gallery <ul>
        lis = driver.find_elements(By.CSS_SELECTOR, 'div#ctl00_ContentPlaceHolderBody_ReorderList1 ul > li')
        for li in lis:
            try:
                a_tag = li.find_element(By.CSS_SELECTOR, 'a[target="_blank"]')
                href = a_tag.get_attribute('href')
                if href and href.startswith('http'):
                    images.append(href)
            except Exception:
                continue
    except Exception as e:
        print(f"[ERROR] Error obteniendo imágenes: {str(e)}")
    finally:
        # Always try to close the secondary tab and return to the main one
        if len(driver.window_handles) > 1:
            try:
                driver.close()
            except Exception as e:
                print(f"[ERROR] Error cerrando ventana secundaria: {str(e)}")
            try:
                driver.switch_to.window(main_window)
                time.sleep(3)  # Añadido tiempo de espera después de volver a la ventana principal
            except Exception as e:
                print(f"[ERROR] Error volviendo a ventana principal: {str(e)}")
    return images

def summarize_description(html):
    """
    Cleans the HTML and extracts key data from an antique product description.
    Returns a concise string with dimensions, materials, provenance, condition, and unique features.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    dims = re.findall(r'(Height|Width|Depth)[^\d]*(\d+[.,]?\d*)["\']? ?\(?([\d.,]+)? ?cm?\)?', text, re.I)
    dims_str = ', '.join([f"{d[0].capitalize()}: {d[1]}{(' ('+d[2]+'cm)') if d[2] else ''}" for d in dims]) if dims else ''
    materials = re.findall(r'(Arbutus|Yew Wood|Mahogany|Oak|Walnut|Bronze|Porcelain|Glass|Marble|Silver|Gold|Ivory|Ebony)', text, re.I)
    materials_str = ', '.join(sorted(set([m.capitalize() for m in materials]))) if materials else ''
    provenance = ''
    prov_match = re.search(r'(made in|originates from|provenance:?|located in) ([A-Za-z ,.-]+)', text, re.I)
    if prov_match:
        provenance = prov_match.group(0)
    elif 'Ireland' in text:
        provenance = 'Ireland'
    features = []
    if 'inlaid' in text.lower():
        features.append('Inlaid decoration')
    if 'crossed ferns' in text.lower():
        features.append('Crossed Ferns motif')
    if 'original condition' in text.lower():
        features.append('Original condition')
    if 'provenance' in text.lower():
        features.append('Provenance available')
    if 'rare' in text.lower():
        features.append('Rare piece')
    features_str = ', '.join(features)
    state = ''
    if 'restored' in text.lower() or 'cleaned' in text.lower() or 'waxed' in text.lower():
        state = 'Restored/Cleaned'
    elif 'original condition' in text.lower():
        state = 'Original condition'
    summary_parts = []
    if dims_str:
        summary_parts.append(dims_str)
    if materials_str:
        summary_parts.append(f"Materials: {materials_str}")
    if provenance:
        summary_parts.append(f"Provenance: {provenance}")
    if features_str:
        summary_parts.append(f"Features: {features_str}")
    if state:
        summary_parts.append(f"State: {state}")
    summary = '; '.join(summary_parts)
    return summary or text[:200]

all_data = []
page = 21  # Página de inicio - Cambiado para comenzar desde la página 21

wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

# Funciones de navegación mejoradas
def navigate_to_page(target_page, max_retries=30):
    print(f"🔍 Intentando navegar a la página {target_page}...")
    for attempt in range(max_retries):
        try:
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")))
            paging_panel = driver.find_element(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
            page_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
            current_elem = paging_panel.find_element(By.CSS_SELECTOR, ".PagingLinkCurrent")
            current_page = int(current_elem.text.strip())
            if current_page == target_page:
                print(f"✅ Ya estamos en la página {target_page}")
                return True

            # Si la página está visible, haz clic directamente
            found = False
            for link in page_links:
                if link.text.strip() == str(target_page):
                    driver.execute_script("arguments[0].scrollIntoView(true);", link)
                    link.click()
                    time.sleep(2)
                    found = True
                    break
            if found:
                current_elem = driver.find_element(By.CSS_SELECTOR, ".PagingLinkCurrent")
                current_page = int(current_elem.text.strip())
                if current_page == target_page:
                    print(f"✅ Navegado a la página {target_page}")
                    return True
                else:
                    print(f"[WARN] No estamos en la página {target_page} (actual: {current_page}), reintentando...")
                    time.sleep(2)
                    continue

            # Si no está visible, puede que necesite pulsar << para mostrar el bloque superior
            while True:
                paging_panel = driver.find_element(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
                page_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
                visible_pages = [l.text.strip() for l in page_links if l.text.strip().isdigit()]
                # Si la página objetivo es mayor que el máximo visible y existe <<, púlsalo
                if visible_pages:
                    max_visible = max([int(p) for p in visible_pages])
                    min_visible = min([int(p) for p in visible_pages])
                    # Si la página objetivo está por delante, pulsa '>>'
                    if target_page > max_visible:
                        rewind_btn = None
                        for link in page_links:
                            if link.get_attribute('id') == 'ctl00_ContentPlaceHolderBody_pagelinkRewind' or link.text.strip() in ['«', '<<']:
                                rewind_btn = link
                                break
                        if rewind_btn:
                            driver.execute_script("arguments[0].scrollIntoView(true);", rewind_btn)
                            rewind_btn.click()
                            time.sleep(2)
                            continue
                    # Si la página objetivo está por detrás, pulsa '<<' hasta que esté visible
                    elif target_page < min_visible:
                        rewind_btn = None
                        for link in page_links:
                            if link.get_attribute('id') == 'ctl00_ContentPlaceHolderBody_pagelinkRewind' or link.text.strip() in ['«', '<<']:
                                rewind_btn = link
                                break
                        if rewind_btn:
                            driver.execute_script("arguments[0].scrollIntoView(true);", rewind_btn)
                            rewind_btn.click()
                            time.sleep(2)
                            continue
                # Si la página está visible tras pulsar <<, haz clic
                if str(target_page) in visible_pages:
                    for link in page_links:
                        if link.text.strip() == str(target_page):
                            driver.execute_script("arguments[0].scrollIntoView(true);", link)
                            link.click()
                            time.sleep(2)
                            current_elem = driver.find_element(By.CSS_SELECTOR, ".PagingLinkCurrent")
                            current_page = int(current_elem.text.strip())
                            if current_page == target_page:
                                print(f"✅ Navegado a la página {target_page}")
                                return True
                            else:
                                print(f"[WARN] No estamos en la página {target_page} (actual: {current_page}), reintentando...")
                                time.sleep(2)
                                break
                    break
                # Si no está visible, busca el botón '>>' y avanza
                avanzar_btn = None
                for link in page_links:
                    if link.text.strip() in ['»', '>>', 'Next', '>|']:
                        avanzar_btn = link
                        break
                if avanzar_btn:
                    driver.execute_script("arguments[0].scrollIntoView(true);", avanzar_btn)
                    avanzar_btn.click()
                    time.sleep(2)
                else:
                    print(f"❌ No se pudo avanzar a la página {target_page} desde la página {current_page}")
                    return False
                attempt += 1
                if attempt >= max_retries:
                    print(f"❌ No se pudo navegar a la página {target_page} después de {max_retries} intentos")
                    return False
        except Exception as e:
            print(f"⚠️ Error en intento {attempt + 1}/{max_retries}: {e}")
            time.sleep(2)
    print(f"❌ No se pudo navegar a la página {target_page} después de {max_retries} intentos")
    return False

def navigate_to_start_page():
    """Navega directamente a la página inicial usando los controles de paginación"""
    print(f"🔍 Navegando a la página inicial {START_PAGE}...")
    
    try:
        driver.get(ITEMS_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(2)
        
        current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
        current_page = int(current_elem.text.strip())
        
        while current_page < START_PAGE:
            next_links = driver.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
            clicked = False
            
            for link in next_links:
                if link.text.strip() in ['»', '>>', 'Next', '>|']:
                    link.click()
                    time.sleep(2)
                    current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                    current_page = int(current_elem.text.strip())
                    print(f"  ⏩ Avanzando a página {current_page}")
                    clicked = True
                    break
                    
            if not clicked:
                print("❌ No se encontró botón de siguiente página")
                return False
                
        print(f"✅ Llegamos a la página objetivo {START_PAGE}")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la navegación: {e}")
        return False

# Iniciar proceso de extracción
print("\n=== INICIANDO PROCESO DE EXTRACCIÓN ===")
print(f"📊 Datos existentes cargados: {len(all_data)} items")
print(f"� Comenzando desde la página {START_PAGE}")

try:
    driver.get(ITEMS_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    time.sleep(2)

    # Navegar directamente a la página de inicio usando la función robusta
    if not navigate_to_page(START_PAGE):
        print(f"❌ No se pudo llegar a la página objetivo {START_PAGE}")
        driver.quit()
        exit(1)

    current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
    current_page = int(current_elem.text.strip())
    print(f"📍 Estamos en la página {current_page}")

    # Verificar que tenemos datos para procesar y añadir más información de diagnóstico
    print("\n=== VERIFICANDO DATOS EN PÁGINA INICIAL ===")
    rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
    print(f"[DEBUG] Filas encontradas en la tabla: {len(rows)}")

    if len(rows) <= 1:
        print("[ERROR] La tabla está vacía o solo contiene el encabezado")
        raise Exception("No se encontraron items para procesar")
    
    # Verificar estructura de la primera fila de datos
    try:
        first_row = rows[1]  # Primera fila después del encabezado
        inner_tables = first_row.find_elements(By.TAG_NAME, "table")
        print(f"[DEBUG] Tablas internas en primera fila: {len(inner_tables)}")
        
        if inner_tables:
            inner_row = inner_tables[0].find_elements(By.TAG_NAME, "tr")[0]
            tds = inner_row.find_elements(By.TAG_NAME, "td")
            print(f"[DEBUG] Columnas encontradas en primera fila: {len(tds)}")
    except Exception as e:
        print(f"[ERROR] Error al inspeccionar estructura de la primera fila: {e}")
        
    print(f"\n=== COMENZANDO EXTRACCIÓN DE DATOS ===")
    print(f"📊 Items en la página actual: {len(rows)-1}")
    
except Exception as e:
    print(f"❌ Error en la inicialización: {e}")
    driver.quit()
    exit(1)

# Configuración de la extracción
backup_size = 100  # Cambia de 200 a 100
final_backup_written = False

def go_to_page(target_page):
    print(f"\n[NAV] Intentando ir a la página {target_page}")
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        try:
            # Verificar si ya estamos en la página correcta
            current = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
            if current.text.strip() == str(target_page):
                print(f"[NAV] Ya estamos en la página {target_page}")
                return True
                
            print(f"[NAV] Intento {attempt}/{max_attempts}")
            paging_panel = driver.find_element(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
            page_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
            for link in page_links:
                try:
                    if link.text.strip() == str(target_page):
                        link.click()
                        WebDriverWait(driver, 10).until(
                            lambda d: d.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent").text.strip() == str(target_page)
                        )
                        # Verifica que realmente estamos en la página correcta
                        current_page_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                        if current_page_elem.text.strip() == str(target_page):
                            return
                except Exception:
                    break  # Si stale, reinicia el while
            else:
                for link in page_links:
                    try:
                        if link.text.strip() in ['»', '>>']:
                            link.click()
                            time.sleep(1)
                            break
                    except Exception:
                        break
                else:
                    raise Exception(f"No se pudo encontrar la página {target_page} en el paginador.")
        except Exception:
            time.sleep(1)
            continue

def get_cell_text(td):
    try:
        return td.find_element(By.TAG_NAME, 'span').text.strip()
    except Exception:
        try:
            return td.text.strip()
        except Exception:
            return ''

try:
    print("\n=== INICIANDO BUCLE PRINCIPAL DE SCRAPING ===")
    print(f"[INFO] Comenzando procesamiento desde página {START_PAGE}")
    
    page = START_PAGE
    # Asegurarse de estar en la página correcta antes de scrapear
    current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
    current_page = int(current_elem.text.strip())
    if current_page != START_PAGE:
        print(f"[INFO] No estamos en la página de inicio ({START_PAGE}), navegando...")
        navigate_to_page(START_PAGE)
        time.sleep(2)
        current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
        current_page = int(current_elem.text.strip())
        if current_page != START_PAGE:
            print(f"[ERROR] No se pudo llegar a la página de inicio {START_PAGE}. Abortando.")
            driver.quit()
            exit(1)
    print(f"[INFO] Confirmado: estamos en la página {current_page} para iniciar el scraping.")
    # Ahora sí, iniciar el bucle principal
    while True:
        try:
            print(f"\n--- Procesando página {page} ---")
            # Navega y verifica que realmente estamos en la página correcta
            for nav_attempt in range(5):
                go_to_page(page)
                time.sleep(2)
                current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                current_page = int(current_elem.text.strip())
                if current_page == page:
                    break
                print(f"[WARN] No estamos en la página {page} (actual: {current_page}), reintentando navegación...")
            else:
                print(f"[FATAL] No se pudo llegar a la página {page} tras varios intentos. Abortando.")
                driver.quit()
                exit(1)

            # SOLO AQUÍ obtén las filas de la tabla
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.gridView")))
            rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
            
            idx = 1
            max_retries_per_row = 3
            
            while idx < len(rows):
                retry_count = 0
                while retry_count < max_retries_per_row:
                    try:
                        # Si necesitas refrescar la página por referencias obsoletas:
                        # driver.refresh()
                        # time.sleep(2)
                        # rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                        
                        row = rows[idx]
                        inner_tables = row.find_elements(By.TAG_NAME, "table")
                        
                        if not inner_tables:
                            print(f"[DEBUG] Fila {idx} no tiene tablas internas")
                            idx += 1
                            continue
                        
                        try:
                            inner_row = inner_tables[0].find_elements(By.TAG_NAME, "tr")[0]
                            tds = inner_row.find_elements(By.TAG_NAME, "td")
                            
                            if len(tds) < 10:
                                print(f"[DEBUG] Fila {idx} no tiene suficientes columnas ({len(tds)} encontradas)")
                                idx += 1
                                continue
                        except Exception as e:
                            print(f"[ERROR] No se pudo acceder a las celdas de la fila {idx}: {str(e)}")
                            idx += 1
                            continue
                        
                        # Verificar que los elementos no estén obsoletos y esperar a que sean interactuables
                        try:
                            # Esperar explícitamente a que el primer elemento sea interactuable
                            wait.until(EC.element_to_be_clickable((By.XPATH, f"//table[@class='gridView']//tr[{idx+1}]")))
                            # Intenta acceder a alguna propiedad para verificar que el elemento sigue válido
                            _ = tds[0].is_displayed()
                        except Exception:
                            print(f"[WARN] Los elementos de la fila {idx} están obsoletos o no son interactuables, reintentando...")
                            retry_count += 1
                            if retry_count >= max_retries_per_row:
                                print(f"[ERROR] No se pudo procesar la fila {idx} después de {max_retries_per_row} intentos")
                                idx += 1
                                break  # Salir del bucle de reintentos
                            time.sleep(WAIT_BETWEEN_ROWS)  # Esperar antes de reintentar
                            continue  # Mantener el mismo índice para reintentar
                        
                        # --- EXTRACCIÓN ROBUSTA DEL ID ---
                        try:
                            id_span = tds[2].find_element(By.XPATH, ".//span[contains(@id, '_RptIdItem')]")
                            item_id = id_span.text.strip()
                        except Exception:
                            item_id = ''
                        print(f"[DEBUG] Extracted item_id: '{item_id}' en página {page}, fila {idx}")

                        if not item_id:
                            print(f"[ERROR] Item sin ID en página {page}, fila {idx}. No se guarda.")
                            idx += 1
                            continue
                        
                        # Extract all cell values BEFORE navigation
                        name = get_cell_text(tds[3])
                        category = get_cell_text(tds[4])
                        pictures = get_cell_text(tds[5])
                        price = get_cell_text(tds[6])
                        try:
                            featured_input = tds[7].find_element(By.TAG_NAME, 'input')
                            featured = 'Yes' if featured_input.is_selected() else 'No'
                        except Exception:
                            featured = 'No'
                        if tds[8].find_elements(By.TAG_NAME, 'select'):
                            status = tds[8].find_element(By.TAG_NAME, 'select').get_attribute('value')
                        else:
                            status = get_cell_text(tds[8])
                        updated = get_cell_text(tds[9])
                        
                        # Get images by opening the secondary page
                        images = get_item_images_from_td(tds[5])
                        images = [img.replace('http://', 'https://', 1) for img in images]
                        main_window = driver.current_window_handle
                        desc_summary = ''
                        edit_input = None
                        
                        # Buscar botón de edición
                        try:
                            # Find input[type='image'] with 'RptEdit' in name
                            for td in tds:
                                edit_inputs = td.find_elements(By.CSS_SELECTOR, "input[type='image']")
                                for inp in edit_inputs:
                                    name_attr = inp.get_attribute('name') or ''
                                    if 'RptEdit' in name_attr:
                                        edit_input = inp
                                        print(f"[DEBUG] Found input[type='image'] with name={name_attr}")
                                        break
                                if edit_input:
                                    break
                            
                            # If not found, look for <a> or <button> with edit-related text/attribute
                            if not edit_input:
                                for td in tds:
                                    links = td.find_elements(By.TAG_NAME, 'a')
                                    for link in links:
                                        link_text = link.text.lower()
                                        link_title = link.get_attribute('title') or ''
                                        if 'edit' in link_text or 'edit' in link_title.lower():
                                            edit_input = link
                                            print(f"[DEBUG] Found <a> with edit-related text or title: {link_text} | {link_title}")
                                            break
                                    if edit_input:
                                        break
                                
                                buttons = td.find_elements(By.TAG_NAME, 'button')
                                for btn in buttons:
                                    btn_text = btn.text.lower()
                                    btn_title = btn.get_attribute('title') or ''
                                    if 'edit' in btn_text or 'edit' in btn_title.lower():
                                        edit_input = btn
                                        print(f"[DEBUG] Found <button> with edit-related text or title: {btn_text} | {btn_title}")
                                        break
                                if edit_input:
                                    break
                        except Exception as e:
                            print(f"[ERROR] Error buscando botón de edición: {str(e)}")
                        
                        # Extraer descripción si se encontró botón de edición
                        if edit_input:
                            try:
                                # Si es <a href=...> abre en nueva pestaña
                                if hasattr(edit_input, 'tag_name') and edit_input.tag_name == 'a':
                                    edit_url = edit_input.get_attribute('href')
                                    if edit_url:
                                        driver.execute_script("window.open(arguments[0]);", edit_url)
                                        driver.switch_to.window(driver.window_handles[-1])
                                        wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")))
                                        desc_elem = driver.find_element(By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")
                                        desc_html = desc_elem.get_attribute('value')
                                        desc_summary = summarize_description(desc_html)
                                        driver.close()
                                        driver.switch_to.window(main_window)
                                        # --- Corrección: restaurar la paginación ---
                                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                                        current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                                        current_page = int(current_elem.text.strip())
                                        if current_page != page:
                                            print(f"[WARN] Después de volver atrás estamos en la página {current_page} (esperada: {page}), navegando de nuevo...")
                                            navigate_to_page(page)
                                            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                                        rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                                    else:
                                        print("      [!] <a> edit button without valid href, skipping description.")
                                else:
                                    # Click tradicional para input[type=image] y <button>
                                    edit_input.click()
                                    wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")))
                                    desc_elem = driver.find_element(By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")
                                    desc_html = desc_elem.get_attribute('value')
                                    desc_summary = summarize_description(desc_html)
                                    driver.back()
                                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                                    current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                                    current_page = int(current_elem.text.strip())
                                    if current_page != page:
                                        print(f"[WARN] Después de volver atrás estamos en la página {current_page} (esperada: {page}), navegando de nuevo...")
                                        navigate_to_page(page)
                                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                                    rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                            except Exception as e:
                                print(f"      [!] Could not extract description: {e}")
                                try:
                                    # Manejar posibles problemas de navegación
                                    if len(driver.window_handles) > 1:
                                        driver.close()
                                        driver.switch_to.window(main_window)
                                        time.sleep(2)
                                    # Si no estamos en la URL correcta, intentar volver
                                    if 'Items.aspx' not in driver.current_url:
                                        print(f"[WARN] Navegación incorrecta detectada. URL actual: {driver.current_url}")
                                        driver.get(ITEMS_URL)
                                        time.sleep(3)
                                        # --- Corrección: restaurar la paginación ---
                                        navigate_to_page(page)
                                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                                        rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                                except Exception as inner_e:
                                    print(f"[ERROR] Error grave de navegación: {inner_e}")
                        else:
                            print(f"      [!] No edit button of type input, <a> or <button> found for this item in any column, skipping description.")
                        
                        item = {
                            'ID': item_id,
                            'Name': name,
                            'Category': category,
                            'Pictures': pictures,
                            'Price': price,
                            'Featured': featured,
                            'Status': status,
                            'Updated': updated,
                            'ImageLinks': images,
                            'DescriptionSummary': desc_summary
                        }

                        # --- Evita duplicados globales de ID ---
                        if not hasattr(globals(), 'seen_ids'):
                            seen_ids = set()
                        if item_id in seen_ids:
                            print(f"[WARN] ID global duplicado: {item_id}. Saltando.")
                        else:
                            all_data.append(item)
                            seen_ids.add(item_id)

                        # --- Backup parcial automático cada backup_size items ---
                        if len(all_data) % backup_size == 0 and len(all_data) > 0:
                            backup_filename = f'output/items_backup_{len(all_data)}.json'
                            with open(backup_filename, 'w', encoding='utf-8') as f:
                                json.dump(all_data, f, ensure_ascii=False, indent=2)
                            print(f"[BACKUP] Guardado backup parcial: {backup_filename} ({len(all_data)} items)")

                        # --- Progreso cada 10 páginas ---
                        if page % 10 == 0:
                            print(f"[PROGRESO] Ya procesadas {page} páginas y {len(all_data)} items.")

                        idx += 1
                        break  # Salir del bucle retry_count después de procesar exitosamente
                    
                    except Exception as e:
                        print(f"[ERROR] Error procesando fila {idx}: {str(e)}")
                        retry_count += 1
                        if retry_count >= max_retries_per_row:
                            idx += 1  # Avanzar a la siguiente fila después de fallar todos los reintentos
                        continue
            
            # Al terminar de procesar todas las filas de la página
            items_this_page = len(rows) - 1  # -1 por el encabezado
            if items_this_page > 0:
                recent_items = all_data[-items_this_page:] if len(all_data) >= items_this_page else all_data
                page_ids = [item['ID'] for item in recent_items]
                print(f"[DEBUG] Página {page} - {items_this_page} items procesados - IDs: {page_ids}")
            else:
                print(f"[DEBUG] Página {page} - No se procesaron items")
                    
            print(f"✅ Página {page} procesada completamente con {len(rows)-1} items encontrados")
            
            # Intentar avanzar a la siguiente página
            next_page = page + 1
            print(f"➡️ Intentando navegar a la página {next_page}")
            # Verifica que realmente navegas a la siguiente página
            for nav_attempt in range(5):
                if navigate_to_page(next_page):
                    current_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                    current_page = int(current_elem.text.strip())
                    if current_page == next_page:
                        page = next_page
                        break
                    print(f"[WARN] No estamos en la página {next_page} (actual: {current_page}), reintentando navegación...")
                    time.sleep(2)
                else:
                    print(f"[WARN] No se pudo navegar a la página {next_page}, reintentando...")
            else:
                print("🔚 No hay más páginas disponibles")
                break

            print(f"📄 Procesando página {page}")
            # ...verificación y scraping de la nueva página...

        except KeyboardInterrupt:
            print("[INTERRUPT] Script interrupted by user. Saving backup...")
            break
        except Exception as e:
            print(f"[ERROR] Error general en la página {page}: {str(e)}")
            try:
                driver.refresh()
                time.sleep(2)
                continue
            except:
                break
finally:
    # Always save a final backup if not already saved for the last chunk
    if all_data and (not final_backup_written or len(all_data) % backup_size != 0):
        backup_filename = f'output/items_backup_final.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data[-(len(all_data)%backup_size or backup_size):], f, ensure_ascii=False, indent=2)
        print(f"Final backup saved: {backup_filename} ({len(all_data) % backup_size or backup_size} records)")
    # Guarda el JSON final
    with open('output/items_all.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Guarda el CSV final
    if all_data:
        with open('output/items_all.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
            writer.writeheader()
            writer.writerows(all_data)
    else:
        print("No data to save.")
    if len(all_data) % backup_size == 0 and len(all_data) > 0:
        print(f"[WARNING] Script ended exactly at a multiple of {backup_size} records ({len(all_data)}). Check pagination and backup logic if unexpected.")
        print(f"[DEBUG] Last page processed: {page}")
        if all_data:
            print(f"[DEBUG] First ID of last backup: {all_data[-backup_size]['ID'] if len(all_data) >= backup_size else all_data[0]['ID']}")
            print(f"[DEBUG] Last recorded ID: {all_data[-1]['ID']}")
    driver.quit()

