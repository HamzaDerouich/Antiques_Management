import pandas as pd
import json

# Read the CSV, skipping blank lines and extra headers
csv_file = 'items_all.csv'
df = pd.read_csv(csv_file, skip_blank_lines=True)

# Remove rows that do not have an ID (these are headers or empty rows)
df = df[df['ID'].notnull() & (df['ID'].astype(str).str.strip() != '')]

# Clean newlines and spaces in columns
for col in df.columns:
    df[col] = df[col].astype(str).str.replace('\n', ' ').str.strip()

# Convert to list of dictionaries
items = df.to_dict(orient='records')

# Save partial backups every 200 records
backup_size = 200
for i in range(0, len(items), backup_size):
    backup_items = items[i:i+backup_size]
    backup_filename = f'items_backup_{i//backup_size+1}.json'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_items, f, ensure_ascii=False, indent=2)
    print(f"Partial backup saved: {backup_filename} ({len(backup_items)} records)")

# Save as complete JSON
with open('items_all.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Saved as items_all.json ({len(items)} records)")
