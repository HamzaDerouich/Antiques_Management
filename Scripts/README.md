# Estructura de Scripts

Esta carpeta contiene los scripts organizados por dominio y función:

- `scraping/`: Extracción de datos web
- `data_processing/`: Procesamiento y conversión de datos
- `config/`: Configuración y credenciales
- `tests/`: Pruebas y validaciones
- `backup/`: Gestión de copias de seguridad

Cada script está nombrado para reflejar su propósito y facilitar la entrega y el mantenimiento.

---

# Antiques Management Project

**Task Completed: Data Cleaning and Project Organization**

The data cleaning and project organization task has been successfully completed. The repository is now available in the cloud:

Repository: https://github.com/HamzaDerouich/Antiques_Management

## Project Structure
```
Antiques.py
CSV_FILES/
    items_all_.csv
    items_all__clean.csv
    4am_migration_items_all__clean.csv
Scripts/
    backup/
        backup_manager.py
    config/
        login_config.py
    data_processing/
        clean_csv_name_column.py
        csv_to_json.py
        data_validator.py
        json_to_woocommerce_csv.py
    output/
        items_all.csv
        items_all.json
        items_backup_final.json
    scraping/
        Antiques_original.py
        antiques_scraper.py
        optimized_scraper.py
        robust_scraper.py
        sequential_scraper.py
        stable_scraper.py
    tests/
        antiques_test.py
        import_pytest.py
```

## Summary
- The main data source (`items_all_.csv`) was cleaned, removing the ID prefix and problematic characters from the Name column, while keeping the ID column unchanged.
- The cleaned file (`items_all__clean.csv`) is ready for migration and professional use.
- The project is fully modular, with scripts organized by functionality (processing, scraping, backup, tests, etc.).
- All changes and files are available in the cloud repository.

---

## Next Objective
Starting today, the main goal is to extract (scrape) all data from the old 4am website to prepare it for migration and use in the new platform. All relevant information will be captured and structured for the new site.

---

This task is now finished. I will begin with the new assignment as described above.
