# Pruebas de importación con pytest
import pytest

def test_import_antiques_scraper():
    try:
        from scraping.antiques_scraper import AntiquesScraper
    except ImportError as e:
        pytest.fail(f"No se pudo importar AntiquesScraper: {e}")

def test_import_backup_manager():
    try:
        from backup.backup_manager import save_partial_backup, save_final_backup
    except ImportError as e:
        pytest.fail(f"No se pudo importar backup_manager: {e}")

def test_import_login_config():
    try:
        import config.login_config
    except ImportError as e:
        pytest.fail(f"No se pudo importar login_config: {e}")

def test_import_csv_to_json():
    try:
        from data_processing.csv_to_json import csv_to_json
    except ImportError as e:
        pytest.fail(f"No se pudo importar csv_to_json: {e}")

def test_import_json_to_woocommerce_csv():
    try:
        from data_processing.json_to_woocommerce_csv import json_to_woocommerce_csv
    except ImportError as e:
        pytest.fail(f"No se pudo importar json_to_woocommerce_csv: {e}")

def test_import_data_validator():
    try:
        from data_processing.data_validator import validate_data
    except ImportError as e:
        pytest.fail(f"No se pudo importar data_validator: {e}")
