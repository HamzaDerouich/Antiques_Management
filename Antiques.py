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
- Selenium, pandas, beautifulsoup4, re, csv
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

# Create output folder if it does not exist
os.makedirs('output', exist_ok=True)

# Initialize browser
service = Service('C:/Drivers/chromedriver.exe')  # Absolute path to chromedriver
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

# 1. Login
driver.get(LOGIN_URL)
wait.until(EC.presence_of_element_located((By.ID, USERNAME_FIELD)))
driver.find_element(By.ID, USERNAME_FIELD).send_keys(USERNAME)
driver.find_element(By.ID, PASSWORD_FIELD).send_keys(PASSWORD)
driver.find_element(By.ID, LOGIN_BUTTON).click()

# 2. Go to items page
wait.until(EC.url_contains("Admin"))
driver.get(ITEMS_URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

def get_item_images_from_td(td):
    images = []
    main_window = driver.current_window_handle
    try:
        link = td.find_element(By.TAG_NAME, 'a')
        img_url = link.get_attribute('href')
        driver.execute_script("window.open(arguments[0]);", img_url)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(1.5)
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
    except Exception:
        pass
    finally:
        # Always try to close the secondary tab and return to the main one
        if len(driver.window_handles) > 1:
            try:
                driver.close()
            except Exception:
                pass
            try:
                driver.switch_to.window(main_window)
            except Exception:
                pass
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
page = 11  # Página de inicio

wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

# Pulsa la flecha >> hasta que la página 11 esté visible y haz click en 11
while True:
    paging_panel = driver.find_element(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
    page_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
    # ¿Está la página 11 visible?
    for link in page_links:
        try:
            if link.text.strip() == str(page):
                link.click()
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent").text.strip() == str(page)
                )
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                break  # Sal del for
        except Exception:
            break  # Si stale, reinicia el while
    else:
        # Si no está visible, pulsa la flecha >>
        for link in page_links:
            try:
                if link.text.strip() in ['»', '>>']:
                    link.click()
                    time.sleep(1)
                    break
            except Exception:
                break  # Si stale, reinicia el while
        else:
            raise Exception(f"No se pudo encontrar la página {page} en el paginador.")
        continue  # Vuelve a buscar la página 11
    break  # Sal del while cuando la página 11 esté activa

backup_size = 100  # Cambia de 200 a 100
final_backup_written = False

def go_to_page(target_page):
    while True:
        try:
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

try:
    while True:

        go_to_page(page)
        print(f"Processing page {page}...")
        time.sleep(1.5)
        rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
        print(f"  Items on this page: {len(rows)}")
        idx = 1  # Siempre empieza en 1 para saltar la cabecera
        while idx < len(rows):
            row = rows[idx]
            inner_tables = row.find_elements(By.TAG_NAME, "table")
            if not inner_tables:
                idx += 1
                continue
            inner_row = inner_tables[0].find_elements(By.TAG_NAME, "tr")[0]
            tds = inner_row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 10:
                idx += 1
                continue
            def get_cell_text(td):
                try:
                    return td.find_element(By.TAG_NAME, 'span').text.strip()
                except Exception:
                    try:
                        return td.text.strip()
                    except Exception:
                        return ''
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
            if edit_input:
                try:
                    # Open in new tab if <a href=...>
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
                        else:
                            print("      [!] <a> edit button without valid href, skipping description.")
                    else:
                        # Always traditional click for input[type=image] and <button>
                        current_page = page
                        edit_input.click()
                        wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")))
                        desc_elem = driver.find_element(By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")
                        desc_html = desc_elem.get_attribute('value')
                        desc_summary = summarize_description(desc_html)
                        driver.back()
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                        go_to_page(current_page)
                        rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                except Exception as e:
                    print(f"      [!] Could not extract description: {e}")
                    try:
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(main_window)
                    except Exception:
                        pass
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

        # Al terminar de procesar la página, muestra los IDs obtenidos en esta página y el número de página
        items_this_page = idx - 1  # idx empieza en 1 y se incrementa al final del bucle
        if items_this_page > 0:
            page_ids = [item['ID'] for item in all_data[-items_this_page:]]
        else:
            page_ids = []
        print(f"[DEBUG] Página {page} - IDs obtenidos: {page_ids}")

        # --- Lógica de paginación robusta mejorada ---
        try:
            paging_panels = driver.find_elements(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
            found_next = False
            for paging_panel in paging_panels:
                # Encuentra el enlace de la página actual
                current = paging_panel.find_element(By.CSS_SELECTOR, 'a.PagingLinkCurrent, [class*=PagingLinkCurrent]')
                current_page_num = int(current.text.strip())
                # Busca el siguiente número de página
                paging_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
                for link in paging_links:
                    txt = link.text.strip()
                    if txt.isdigit() and int(txt) == current_page_num + 1:
                        print(f"Moving to next page: {current_page_num + 1}")
                        link.click()
                        WebDriverWait(driver, 20).until(EC.staleness_of(paging_panel))
                        page += 1
                        found_next = True
                        break
                if found_next:
                    break
                # Si no hay siguiente número, busca '»', '>>', 'Next'
                for link in paging_links:
                    if link.text.strip() in ['»', '>>', 'Next']:
                        print(f"Advancing to next block of pages with {link.text.strip()}")
                        link.click()
                        WebDriverWait(driver, 20).until(EC.staleness_of(paging_panel))
                        page += 1
                        found_next = True
                        break
                if found_next:
                    break
            if not found_next:
                print("No more pages. Scraping finished.")
                break
        except Exception as e:
            print(f"No more pages or error: {e}")
            break
        # --- Vuelve a obtener los rows para la nueva página ---
        rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")

        # ...después de cargar la página o volver de una edición...
        try:
            current_page_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
            current_page_real = int(current_page_elem.text.strip())
            if current_page_real != page:
                print(f"[FIX] Página real {current_page_real} no coincide con esperada {page}. Corrigiendo...")
                # Intenta forzar por URL (si la web lo permite)
                try:
                    driver.get(f"https://4am.ie/Admin/Items.aspx?page={page}")
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    current_page_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                    current_page_real = int(current_page_elem.text.strip())
                except Exception:
                    pass
                # Si aún no coincide, intenta hacer click en el paginador
                if current_page_real != page:
                    page_links = driver.find_elements(By.CSS_SELECTOR, "a.PagingLink")
                    for link in page_links:
                        if link.text.strip() == str(page):
                            link.click()
                            time.sleep(2)
                            break
                    # Verifica una vez más
                    current_page_elem = driver.find_element(By.CSS_SELECTOR, "a.PagingLinkCurrent")
                    current_page_real = int(current_page_elem.text.strip())
                    if current_page_real != page:
                        raise Exception(f"No se pudo corregir la página. Página real: {current_page_real}, esperada: {page}")
        except Exception as e:
            print(f"[ERROR][PAGINACIÓN] No se pudo verificar/corregir la página: {e}")
            continue
except KeyboardInterrupt:
    print("[INTERRUPT] Script interrupted by user. Saving backup...")
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

