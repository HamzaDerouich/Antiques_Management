import csv
import json
import os

def csv_to_json(csv_path, json_path):
    """Convierte un archivo CSV en un archivo JSON."""
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
    with open(json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=2)
    print(f"[DATA] CSV convertido a JSON: {json_path}")

if __name__ == "__main__":
    csv_path = 'output/items_all.csv'
    json_path = 'output/items_all.json'
    csv_to_json(csv_path, json_path)
