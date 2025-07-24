import csv
import re

def clean_name(name, id_value):
    """
    Elimina el prefijo de ID del Name y caracteres raros.
    Ejemplo: 'M178 Pair of Framed...' -> 'Pair of Framed...'
    """
    pattern = rf'^"?{re.escape(id_value)}[\s,-]*'
    name = re.sub(pattern, '', name)
    name = re.sub(r'[^\w\s.,;:()\-\'\"]+', '', name)
    return name.strip()

def process_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            if not row or len(row) < 2:
                writer.writerow(row)
                continue
            id_value = row[0]
            name_value = row[1]
            cleaned_name = clean_name(name_value, id_value)
            row[1] = cleaned_name
            writer.writerow(row)

if __name__ == "__main__":
    input_csv = "CSV_FILES/items_all_.csv"
    output_csv = "CSV_FILES/items_all__clean.csv"
    process_csv(input_csv, output_csv)
