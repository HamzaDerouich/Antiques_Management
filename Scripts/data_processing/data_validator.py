import json
import os

def validate_data(json_path):
    """Valida los datos extraídos y muestra posibles problemas."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    errors = []
    for idx, item in enumerate(data):
        if not item.get('ID') or not item.get('Name'):
            errors.append((idx, item))
    if errors:
        print(f"[VALIDATOR] Se encontraron {len(errors)} items con problemas de ID o Name:")
        for idx, item in errors:
            print(f"  - Fila {idx}: {item}")
    else:
        print("[VALIDATOR] Todos los items tienen ID y Name válidos.")

if __name__ == "__main__":
    json_path = 'output/items_all.json'
    validate_data(json_path)
