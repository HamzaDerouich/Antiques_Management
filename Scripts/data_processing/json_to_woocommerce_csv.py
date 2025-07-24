import json
import csv
import os

def json_to_woocommerce_csv(json_path, csv_path):
    """Convierte un archivo JSON en un CSV compatible con WooCommerce."""
    with open(json_path, 'r', encoding='utf-8') as jsonfile:
        data = json.load(jsonfile)
    if not data:
        print("No hay datos para convertir.")
        return
    with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"[DATA] JSON convertido a CSV WooCommerce: {csv_path}")

if __name__ == "__main__":
    json_path = 'output/items_all.json'
    csv_path = 'output/items_woocommerce.csv'
    json_to_woocommerce_csv(json_path, csv_path)
