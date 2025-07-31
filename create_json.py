
import pandas as pd
import json

# Lecture du CSV
df = pd.read_csv("data.csv")

# Dictionnaire temporaire pour stocker les infos par table
tables_info = {}

# Parcourir chaque ligne pour collecter colonnes et colonnes sources
for _, row in df.iterrows():
    target_table = row['target_table']
    target_field = row['target_field']
    source_field = row['source_field']

    # === Gestion target_table ===
    if target_table not in tables_info:
        tables_info[target_table] = {
            "layer": row['layer'],
            "sub_layer": row['sub_layer'],
            "columns": set(),
            "columns_source": set()
        }

    # Ajouter les colonnes propres à la target_table
    if pd.notna(target_field):
        tables_info[target_table]["columns"].add(target_field)
    if pd.notna(source_field):
        tables_info[target_table]["columns_source"].add(source_field)

    # === Gestion source_table (peut contenir plusieurs sources séparées par ",") ===
    if pd.notna(row['source_table']):
        source_tables = [src.strip() for src in row['source_table'].split(",")]  # split multi-sources

        for src_table in source_tables:
            if src_table not in tables_info:
                tables_info[src_table] = {
                    "layer": None,  # Pas toujours dispo dans CSV
                    "sub_layer": None,
                    "columns": set(),
                    "columns_source": set()
                }
            # Ajouter la colonne source dans la table source
            if pd.notna(source_field):
                tables_info[src_table]["columns"].add(source_field)

# === Construire les noeuds enrichis ===
nodes = [
    {
        "id": table,
        "layer": info["layer"],
        "sub_layer": info["sub_layer"],
        "columns": sorted(list(info["columns"])),
        "columns_source": sorted(list(info["columns_source"]))
    }
    for table, info in tables_info.items()
]

# === Préparation des edges (relations source -> target) ===
edges = {}
for _, row in df.iterrows():
    if pd.notna(row['source_table']):
        source_tables = [src.strip() for src in row['source_table'].split(",")]  # gestion multi-sources
        for src in source_tables:
            key = (src, row['target_table'])
            if key not in edges:
                edges[key] = {
                    "source": src,
                    "target": row['target_table'],
                    "columns": []
                }
            if pd.notna(row['source_field']):
                edges[key]["columns"].append(row['source_field'])

edges_list = list(edges.values())

# === Construire le JSON final enrichi ===
network_json = {
    "nodes": nodes,
    "edges": edges_list
}

# === Sauvegarde ===
with open("network.json", "w", encoding="utf-8") as f:
    json.dump(network_json, f, indent=4, ensure_ascii=False)

print("✅ Fichier network.json enrichi généré avec succès (avec les nouveaux noms)")

