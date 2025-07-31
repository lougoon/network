import pandas as pd
import json

# Lecture du CSV
df = pd.read_csv("data.csv")

# Nettoyage : supprimer espaces inutiles dans les noms
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Dictionnaire temporaire pour stocker les infos par table
tables_info = {}

for _, row in df.iterrows():
    target_table = row['target_table']
    target_field = row['target_field']
    source_field = row['source_field']
    source_tables = str(row['source_table']).split(",") if pd.notna(row['source_table']) else [None]
    source_tables = [t.strip() for t in source_tables if t and t.strip()]

    # === Ajouter ou créer la table cible ===
    if target_table not in tables_info:
        tables_info[target_table] = {
            "layer": row['layer'],
            "sub_layer": row['sub_layer'],
            "columns": [],             # Liste des champs target
            "columns_source": []       # Liste des champs source alignés avec target
        }

    # Chaque target_field est lié directement à son source_field
    tables_info[target_table]["columns"].append(target_field if pd.notna(target_field) else "")
    tables_info[target_table]["columns_source"].append(source_field if pd.notna(source_field) else "")

    # === Ajouter les tables sources ===
    for src_table in source_tables:
        if src_table:  # Sauter si None
            if src_table not in tables_info:
                tables_info[src_table] = {
                    "layer": None,  # Pas toujours dispo dans le CSV
                    "sub_layer": None,
                    "columns": [],
                    "columns_source": []
                }
            # Ajouter la colonne source dans la table source elle-même
            if pd.notna(source_field):
                tables_info[src_table]["columns"].append(source_field)
                tables_info[src_table]["columns_source"].append("")  # Pas de source pour ces colonnes

# === Construire la liste des noeuds ===
nodes = []
for table, info in tables_info.items():
    nodes.append({
        "id": table,
        "layer": info["layer"],
        "sub_layer": info["sub_layer"],
        "columns": info["columns"],  # Garder l'ordre exact
        "columns_source": info["columns_source"]
    })

# === Construire les edges (relations source -> target) ===
edges = {}
for _, row in df.iterrows():
    if pd.notna(row['source_table']):
        for src_table in str(row['source_table']).split(","):
            src_table = src_table.strip()
            key = (src_table, row['target_table'])
            if key not in edges:
                edges[key] = {
                    "source": src_table,
                    "target": row['target_table'],
                    "columns": []
                }
            if pd.notna(row['source_field']):
                edges[key]["columns"].append(row['source_field'])

edges_list = list(edges.values())

# === Sauvegarde JSON ===
network_json = {"nodes": nodes, "edges": edges_list}
with open("network.json", "w", encoding="utf-8") as f:
    json.dump(network_json, f, indent=4, ensure_ascii=False)

print("✅ Nouveau fichier network.json enrichi et corrigé généré avec succès")


