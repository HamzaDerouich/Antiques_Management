import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from bs4 import BeautifulSoup
import re

# CONFIGURATION
LOGIN_URL = "https://4am.ie/Logon.aspx?admin&ReturnUrl=%2fAdmin%2fItems.aspx"
ITEMS_URL = "https://4am.ie/Admin/Items.aspx"
USERNAME = "martinfennelly@gmail.com"
PASSWORD = "martinfennelly"  # <--- ENTER YOUR PASSWORD
USERNAME_FIELD = "ctl00_ContentPlaceHolderBody_username"
PASSWORD_FIELD = "ctl00_ContentPlaceHolderBody_password"
LOGIN_BUTTON = "ctl00_ContentPlaceHolderBody_Button1"

service = Service('C:/Drivers/chromedriver.exe')
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

def summarize_description(html):
    """
    Cleans the HTML and extracts key data from the description of an antique product.
    Returns a concise string with dimensions, materials, provenance, condition, and unique features.
    """
    # 1. Clean HTML
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)

    # 2. Find dimensions
    dims = re.findall(r'(Height|Width|Depth)[^\d]*(\d+[.,]?\d*)["\']? ?\(?([\d.,]+)? ?cm?\)?', text, re.I)
    dims_str = ', '.join([f"{d[0].capitalize()}: {d[1]}{(' ('+d[2]+'cm)') if d[2] else ''}" for d in dims]) if dims else ''

    # 3. Find materials
    materials = re.findall(r'(Arbutus|Yew Wood|Mahogany|Oak|Walnut|Bronze|Porcelain|Glass|Marble|Silver|Gold|Ivory|Ebony)', text, re.I)
    materials_str = ', '.join(sorted(set([m.capitalize() for m in materials]))) if materials else ''

    # 4. Provenance
    provenance = ''
    prov_match = re.search(r'(made in|originates from|provenance:?|located in) ([A-Za-z ,.-]+)', text, re.I)
    if prov_match:
        provenance = prov_match.group(0)
    elif 'Ireland' in text:
        provenance = 'Ireland'

    # 5. Unique features
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

    # 6. Condition
    state = ''
    if 'restored' in text.lower() or 'cleaned' in text.lower() or 'waxed' in text.lower():
        state = 'Restored/Cleaned'
    elif 'original condition' in text.lower():
        state = 'Original condition'

    # 7. Summarize
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
    return summary or text[:200]  # fallback: first 200 characters

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
        lis = driver.find_elements(By.CSS_SELECTOR, 'div#ctl00_ContentPlaceHolderBody_ReorderList1 ul > li')
        for li in lis:
            try:
                a_tag = li.find_element(By.CSS_SELECTOR, 'a[target="_blank"]')
                href = a_tag.get_attribute('href')
                if href and href.startswith('http'):
                    # Change http to https
                    images.append(href.replace('http://', 'https://', 1))
            except Exception:
                continue
    except Exception:
        pass
    finally:
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

all_data = []
page = 1
while True:
    print(f"Processing page {page}...")
    time.sleep(1.5)
    rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
    print(f"  Items on this page: {len(rows)}")
    idx = 1  # Start from 1, not 0, to skip header row
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
        # Extract all cell values BEFORE any navigation
        item_id = get_cell_text(tds[2])
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
        images = get_item_images_from_td(tds[5])
        # --- START: Extract and summarize description ---
        main_window = driver.current_window_handle
        desc_summary = ''
        edit_input = None
        for col_idx, td in enumerate(tds):
            edit_inputs = td.find_elements(By.CSS_SELECTOR, "input[type='image']")
            for inp in edit_inputs:
                name_attr = inp.get_attribute('name') or ''
                if 'RptEdit' in name_attr:
                    edit_input = inp
                    break
            if edit_input:
                break
        if edit_input:
            try:
                edit_input.click()
                wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")))
                desc_elem = driver.find_element(By.NAME, "ctl00$ContentPlaceHolderBody$txtdesc")
                desc_html = desc_elem.get_attribute('value')
                desc_summary = summarize_description(desc_html)
                driver.back()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                # Re-fetch rows after navigation
                rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
            except Exception as e:
                print(f"      [!] Could not extract description: {e}")
                try:
                    driver.back()
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    rows = driver.find_elements(By.CSS_SELECTOR, "table.gridView > tbody > tr")
                except Exception:
                    pass
        else:
            print(f"      [!] No input type edit button found for this item in any column, skipping description.")
        # --- END: Extract and summarize description ---
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
        all_data.append(item)
        idx += 1
    # Find the next page link by number, not by sibling
    try:
        paging_panel = driver.find_element(By.ID, "ctl00_ContentPlaceHolderBody_PanelDataListPaging")
        paging_links = paging_panel.find_elements(By.CSS_SELECTOR, 'a.PagingLink')
        found_next = False
        for link in paging_links:
            if link.text.strip().isdigit() and int(link.text.strip()) == page + 1:
                print(f"Moving to next page: {page+1}")
                link.click()
                page += 1
                found_next = True
                break
        if not found_next:
            # Try to find a "Next" or "»" link
            for link in paging_links:
                if link.text.strip().lower() in ['next', '»', '>>']:
                    print(f"Moving to next page (Next/»): {page+1}")
                    link.click()
                    page += 1
                    found_next = True
                    break
        if not found_next:
            print("No more pages. Scraping finished.")
            break
    except Exception as e:
        print(f"No more pages or error: {e}")
        break

# Save to CSV (without duplicating headers and with correct ImageLinks format)
with open('items_test20.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['ID', 'Name', 'Category', 'Pictures', 'Price', 'Featured', 'Status', 'Updated', 'ImageLinks', 'DescriptionSummary']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for item in all_data:
        # Format ImageLinks as a string of URLs separated by comma and space
        images = item['ImageLinks']
        if isinstance(images, list):
            images_str = ', '.join(images)
        else:
            images_str = str(images)
        row = item.copy()
        row['ImageLinks'] = images_str
        writer.writerow(row)

# Save to JSON directly
with open('items_test20.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"Test extraction completed! {len(all_data)} records saved to items_test20.csv and items_test20.json")
driver.quit()

# --- FUNCTION TEST ---
if __name__ == "__main__":
    # Example usage with a description HTML (you can replace with the real one)
    html = '''<p><span id="cont_LabelItemDescription" style="color:#21455B;"> </span></p>
<p style="text-align: center"><span style="font-size: medium;"> </span></p>
<p style="text-align: center"><span style="font-size: medium;"> </span></p>
<p>&nbsp;</p>
<div class="OutlineElement Ltr SCXW53874507" style="...">
<p class="Paragraph SCXW53874507" style="..." lang="EN-US"><a class="Hyperlink SCXW53874507" href="http://www.fennelly.net/glossary.aspx#K" target="_blank" rel="noreferrer" style="..."><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Rare Piece of Irish History for Sale at my Gallery on Francis Street Dublin</span></span></a><span class="EOP SCXW53874507" data-ccp-props="{&quot;201341983&quot;:0,&quot;335551550&quot;:2,&quot;335551620&quot;:2,&quot;335559739&quot;:160,&quot;335559740&quot;:259}" style="...">&nbsp;</span></p>
</div>
<div class="OutlineElement Ltr SCXW53874507" style="...">
<p class="Paragraph SCXW53874507" style="..." lang="EN-US"><a class="Hyperlink SCXW53874507" href="http://www.fennelly.net/glossary.aspx#K" target="_blank" rel="noreferrer" style="..."><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Irish Killarneyware</span></span></a><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">&nbsp;</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Ta</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">ble&nbsp;Circa</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="..."><span>&nbsp;</span></span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">1</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">8</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">70&nbsp;&ndash;</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="..."><span>&nbsp;</span></span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Museum&nbsp;</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Q</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">u</span></span><span class="TextRun Underlined SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">ality</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="..."> This </span>piece of Irish History is truly Stunning and in some expert opinions, the best Killarney Table currently for Sale. It was made in Co Kerry Ireland in the late 19th Century by most likely the famed Killarney maker, Egan, bearing the Rare Crossed Ferns Motif to the&nbsp;</span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">center</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">&nbsp;top. It is constructed from Arbutus and Yew Wood and has the full spectrum of Irish Imagery Ferns, Shamrocks, Harps and Buildings from the Muckross area outside Killarney, Co. Kerry. The Table is in full original condition and was recently cleaned and Waxed by our restoration experts. The Table can be displayed in an upright position (see&nbsp;pic 2) as it flips on its Column base which also bears inlaid Irish&nbsp;Imagery. The Column tapers from the top to a central octagonal design with alternate Harp and Shamrock inlay. The Table is raised on a spreading base with&nbsp;four&nbsp;scrolled feet.&nbsp;When it comes to a beautiful piece of Irish Furniture and also an investment item these pieces of Killarney are perfect, especially when they are as detailed and rare as this one. There is super detail on this piece and this puts this Table way above some plainer pieces that you may find. Full&nbsp;Provenance&nbsp;available with this piece and please note the Large dimensions for Shipping. I was&nbsp;fortunate to&nbsp;locate this one here in Ireland as many have found their way to the USA over the years</span></span></p>
</div>
<div class="OutlineElement Ltr SCXW53874507" style="...">
<p class="Paragraph SCXW53874507" style="..." lang="EN-US"><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Height&nbsp;</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">28.5" (72.5cm) Max&nbsp;</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">Width&nbsp;</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">59" (150cm)</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">&nbsp;Depth&nbsp;</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">43.5" (110cm</span></span><span class="TextRun SCXW53874507" style="..." lang="EN-US"><span class="NormalTextRun SCXW53874507" style="...">) Item Sold</span></span></p>
</div>'''
    resumen = summarize_description(html)
    print("Generated summary:", resumen)
