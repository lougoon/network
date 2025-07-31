import streamlit as st
import json
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# === Fonction pour construire un graphe Plotly interactif avec flèches ===
def build_plotly_network(G, pos, node_layers, selected_layers, selected_sub_layers):
    node_x, node_y, node_text, node_color, node_ids = [], [], [], [], []

    for node in G.nodes():
        layer = node_layers[node]["layer"]
        sub_layer = node_layers[node]["sub_layer"]

        if (layer in selected_layers or layer is None) and (sub_layer in selected_sub_layers or sub_layer is None):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node} (Layer: {layer}, Sub-layer: {sub_layer})")
            node_ids.append(node)
            color_map = {"bronze": "brown", "silver": "gray", "gold": "gold", None: "lightblue"}
            node_color.append(color_map.get(layer, "lightblue"))

    edge_traces = []
    for edge in G.edges():
        if edge[0] in node_ids and edge[1] in node_ids:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            # Ligne de base
            edge_traces.append(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                line=dict(width=1, color="#888"),
                mode="lines",
                hoverinfo="none"
            ))

            # Ajout de la flèche (petit triangle à la fin)
            arrow_x = x0 + 0.85 * (x1 - x0)
            arrow_y = y0 + 0.85 * (y1 - y0)
            edge_traces.append(go.Scatter(
                x=[arrow_x], y=[arrow_y],
                mode="markers",
                marker=dict(symbol="triangle-up", size=8, angleref="previous", anglemode="anchor",
                            angle=nx.utils.arctan2(y1-y0, x1-x0) * 180 / 3.14159,
                            color="#888"),
                hoverinfo="none"
            ))

    # Tracer les nœuds
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=[n for n in node_ids],
        textposition="top center",
        marker=dict(size=18, color=node_color, line_width=2),
        textfont=dict(color="white"),
        hoverinfo="text",
    )

    fig = go.Figure(data=edge_traces + [node_trace],
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

# Préparer le graphe initial complet
G_full = nx.DiGraph()
node_layers = {}

for node in network_json["nodes"]:
    G_full.add_node(node["id"])
    node_layers[node["id"]] = {
        "layer": node["layer"],
        "sub_layer": node["sub_layer"],
        "columns": node["columns"],
        "columns_source": node["columns_source"]
    }

for edge in network_json["edges"]:
    G_full.add_edge(edge["source"], edge["target"], columns=edge.get("columns", []))

# === Filtres Sidebar ===
st.sidebar.header("Filtres")
layers = sorted({n["layer"] for n in network_json["nodes"] if n["layer"]})
sub_layers = sorted({n["sub_layer"] for n in network_json["nodes"] if n["sub_layer"]})
selected_layers = st.sidebar.multiselect("Layers :", options=layers, default=layers)
selected_sub_layers = st.sidebar.multiselect("Sub-layers :", options=sub_layers, default=sub_layers)

# Sélecteur manuel de table
node_ids_all = sorted([n["id"] for n in network_json["nodes"]])
selected_node_sidebar = st.sidebar.selectbox("🔍 Sélection manuelle d'une table :", options=[""] + node_ids_all)

# === Construire le graphe filtré ===
if selected_node_sidebar:
    # Sous-graphe : table sélectionnée et ses voisins directs
    neighbors = list(G_full.predecessors(selected_node_sidebar)) + list(G_full.successors(selected_node_sidebar))
    subgraph_nodes = [selected_node_sidebar] + neighbors
    G = G_full.subgraph(subgraph_nodes).copy()
else:
    G = G_full.copy()

pos = nx.spring_layout(G, seed=42, k=0.5)

# === Graphe interactif ===
fig, node_ids = build_plotly_network(G, pos, node_layers, selected_layers, selected_sub_layers)
selected_points = plotly_events(fig, click_event=True, hover_event=False)

# === Sélection par clic sur un nœud ===
if selected_points:
    clicked_idx = selected_points[0]["pointIndex"]
    clicked_node_id = node_ids[clicked_idx]
    node_data = next((n for n in network_json["nodes"] if n["id"] == clicked_node_id), None)
    if node_data:
        display_columns_table(node_data)
        # Recentrer le graphe sur ce nœud et ses voisins
        neighbors = list(G_full.predecessors(clicked_node_id)) + list(G_full.successors(clicked_node_id))
        subgraph_nodes = [clicked_node_id] + neighbors
        G = G_full.subgraph(subgraph_nodes).copy()
        pos = nx.spring_layout(G, seed=42, k=0.5)
        fig, _ = build_plotly_network(G, pos, node_layers, selected_layers, selected_sub_layers)
        st.plotly_chart(fig, use_container_width=True)


