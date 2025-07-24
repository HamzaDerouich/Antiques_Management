# Script para gestión de copias de seguridad
import json
import os

def save_partial_backup(all_data, backup_size):
    """
    Guarda un backup parcial cada 'backup_size' items.
    """
    if len(all_data) % backup_size == 0 and len(all_data) > 0:
        backup_filename = f'output/items_backup_{len(all_data)}.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"[BACKUP] Guardado backup parcial: {backup_filename} ({len(all_data)} items)")

def save_final_backup(all_data, backup_size):
    """
    Guarda el backup final al terminar el scraping.
    """
    if all_data and (len(all_data) % backup_size != 0):
        backup_filename = f'output/items_backup_final.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data[-(len(all_data)%backup_size or backup_size):], f, ensure_ascii=False, indent=2)
        print(f"Final backup saved: {backup_filename} ({len(all_data) % backup_size or backup_size} records)")
