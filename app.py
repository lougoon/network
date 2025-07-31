import streamlit as st
import json
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# === Fonction pour construire un graphe Plotly interactif ===
def build_plotly_network(G, pos, node_layers, selected_layers, selected_sub_layers, focus_node=None):
    node_x, node_y, node_color, node_ids = [], [], [], []

    # Si focus_node est choisi, on restreint le graphe à ce node + ses voisins
    sub_nodes = set(G.nodes()) if not focus_node else {focus_node} | set(G.predecessors(focus_node)) | set(G.successors(focus_node))

    for node in G.nodes():
        if node not in sub_nodes:
            continue
        layer = node_layers[node]["layer"]
        sub_layer = node_layers[node]["sub_layer"]
        if (layer in selected_layers or layer is None) and (sub_layer in selected_sub_layers or sub_layer is None):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_ids.append(node)
            color_map = {"bronze": "brown", "silver": "gray", "gold": "gold", None: "lightblue"}
            node_color.append(color_map.get(layer, "lightblue"))

    # Tracer les arêtes avec points directionnels
    edge_x, edge_y = [], []
    mid_x, mid_y = [], []  # points pour indiquer la direction
    for edge in G.edges():
        if edge[0] in node_ids and edge[1] in node_ids:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            mid_x.append((x0 + x1) / 2)
            mid_y.append((y0 + y1) / 2)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.8, color="#888"),
        hoverinfo="none",
        mode="lines"
    )

    # Points directionnels
    direction_trace = go.Scatter(
        x=mid_x, y=mid_y,
        mode="markers",
        marker=dict(size=6, color="red", symbol="triangle-up"),  # Petits triangles rouges
        hoverinfo="none"
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_ids,
        textposition="top center",
        marker=dict(size=18, color=node_color, line_width=2),
        textfont=dict(color="white"),
        hoverinfo="text"
    )

    fig = go.Figure(data=[edge_trace, direction_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode="closest",
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor="#222"
                    ))
    return fig, node_ids

# === Fonction pour afficher les colonnes d'un nœud ===
def display_columns_table(node_data):
    if node_data:
        st.subheader(f"📋 Champs de `{node_data['id']}`")
        max_len = max(len(node_data["columns"]), len(node_data["columns_source"]))
        cols_padded = node_data["columns"] + [""] * (max_len - len(node_data["columns"]))
        cols_src_padded = node_data["columns_source"] + [""] * (max_len - len(node_data["columns_source"]))
        df_cols = pd.DataFrame({"Champs (target_field)": cols_padded, "Champs Source (source_field)": cols_src_padded})
        st.dataframe(df_cols, use_container_width=True)

# === Application Streamlit ===
st.set_page_config(layout="wide", page_title="Réseau DB - NetworkX + Plotly")
st.title("📊 Réseau de Tables - Database Lineage (NetworkX + Plotly)")

# Charger le JSON
with open("network.json", "r", encoding="utf-8") as f:
    network_json = json.load(f)

# --- Préparer le graphe NetworkX ---
G = nx.DiGraph()
node_layers = {}

for node in network_json["nodes"]:
    G.add_node(node["id"])
    node_layers[node["id"]] = {
        "layer": node["layer"],
        "sub_layer": node["sub_layer"],
        "columns": node["columns"],
        "columns_source": node["columns_source"]
    }

for edge in network_json["edges"]:
    G.add_edge(edge["source"], edge["target"], columns=edge.get("columns", []))

pos = nx.spring_layout(G, seed=42, k=0.5)

# --- Filtres Sidebar ---
st.sidebar.header("Filtres")
layers = sorted({n["layer"] for n in network_json["nodes"] if n["layer"]})
sub_layers = sorted({n["sub_layer"] for n in network_json["nodes"] if n["sub_layer"]})
selected_layers = st.sidebar.multiselect("Layers :", options=layers, default=layers)
selected_sub_layers = st.sidebar.multiselect("Sub-layers :", options=sub_layers, default=sub_layers)

# --- Sélecteur manuel pour focus ---
node_ids_all = sorted([n["id"] for n in network_json["nodes"]])
focus_node = st.sidebar.selectbox("🔍 Focus sur une table :", options=[""] + node_ids_all)
focus_node = focus_node if focus_node else None

# --- Graphe interactif ---
fig, node_ids = build_plotly_network(G, pos, node_layers, selected_layers, selected_sub_layers, focus_node)
selected_points = plotly_events(fig, click_event=True, hover_event=False)

# --- Sélection par clic ---
if selected_points:
    clicked_idx = selected_points[0]["pointIndex"]
    clicked_node_id = node_ids[clicked_idx]
    node_data = next((n for n in network_json["nodes"] if n["id"] == clicked_node_id), None)
    if node_data:
        display_columns_table(node_data)
        focus_node = clicked_node_id  # Recentrer sur ce noeud

