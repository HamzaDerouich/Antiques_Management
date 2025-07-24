# -*- coding: utf-8 -*-
"""
Antiques.py (Original Backup)
----------------------------
Backup of the original main scraper before refactoring.
"""
# Original code below:

# ...existing code...

# (Full code from Antiques.py is backed up here for reference)

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

# ...rest of the code from Antiques.py...
