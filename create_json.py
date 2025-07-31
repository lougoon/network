import pandas as pd
import json

# Lecture du CSV
df = pd.read_csv("data.csv")

# Dictionnaire temporaire pour stocker les infos par table
tables_info = {}

# Parcourir chaque ligne pour collecter colonnes et colonnes sources
for _, row in df.iterrows():
    # Table target
    table_tgt = row['table_target']
    if table_tgt not in tables_info:
        tables_info[table_tgt] = {
            "layer": row['layer'],
            "sub_layer": row['sub_layer'],
            "columns": set(),
            "columns_source": set()
        }
    # Ajouter les colonnes de target
    if pd.notna(row['col_name']):
        tables_info[table_tgt]["columns"].add(row['col_name'])
    if pd.notna(row['col_name_source']):
        tables_info[table_tgt]["columns_source"].add(row['col_name_source'])

    # Table source (si existe)
    if pd.notna(row['table_source']):
        table_src = row['table_source']
        if table_src not in tables_info:
            tables_info[table_src] = {
                "layer": None,  # Pas toujours dispo dans le CSV
                "sub_layer": None,
                "columns": set(),
                "columns_source": set()
            }
        # Ajouter colonnes source pour la table source
        if pd.notna(row['col_name_source']):
            tables_info[table_src]["columns"].add(row['col_name_source'])

# Préparer les noeuds enrichis
nodes = []
for table, info in tables_info.items():
    nodes.append({
        "id": table,
        "layer": info["layer"],
        "sub_layer": info["sub_layer"],
        "columns": sorted(list(info["columns"])),           # Conversion set -> list
        "columns_source": sorted(list(info["columns_source"]))
    })

# Préparation des edges (relations source -> target)
edges = {}
for _, row in df.iterrows():
    if pd.notna(row['table_source']):
        key = (row['table_source'], row['table_target'])
        if key not in edges:
            edges[key] = {
                "source": row['table_source'],
                "target": row['table_target'],
                "columns": []
            }
        if pd.notna(row['col_name_source']):
            edges[key]["columns"].append(row['col_name_source'])

edges_list = list(edges.values())

# Construire le JSON final enrichi
network_json = {
    "nodes": nodes,
    "edges": edges_list
}

# Sauvegarde
with open("network.json", "w", encoding="utf-8") as f:
    json.dump(network_json, f, indent=4, ensure_ascii=False)

print("✅ Fichier network.json enrichi généré avec succès")

