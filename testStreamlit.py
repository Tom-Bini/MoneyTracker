import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# Connexion à la base de données
def connect_db():
    return sqlite3.connect('DatabaseV1.db')

# Récupérer les données depuis la base de données
def get_data(query):
    conn = connect_db()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Fonction pour afficher le graphique camembert
def pie_chart(df):
    grouped = df.groupby('type').agg({'value_in_EUR':'sum'}).reset_index()
    fig = px.pie(
        grouped, 
        names='type', 
        values='value_in_EUR', 
        title="Répartition des assets par type",
        color='type',
        color_discrete_map={'BTC': 'gold','Altcoins':'cyan','DeFi':'magenta','Fiat':'grey'}
    )
    st.plotly_chart(fig)

# Fonction pour afficher le graphique de la valeur totale en €
def line_chart(df):
    fig = px.line(
        df, 
        x='timestamp', 
        y='total_value_in_EUR', 
        title="Évolution de la valeur totale en €"
    )
    st.plotly_chart(fig)

def main():
    st.title("Money Tracker Dashboard")

    # 1) On charge tous les assets récents
    df = get_data("SELECT * FROM assets WHERE timestamp >= '2025-01-01'")

    # On convertit la colonne timestamp en datetime (format "YYYY-MM-DD HH")
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H")

    # 2) Graphique de l'évolution
    # On agrège pour la line chart
    df_value = (
        df
        .groupby('timestamp')['value_in_EUR']
        .sum()
        .reset_index(name='total_value_in_EUR')
        .sort_values('timestamp')
    )

    st.subheader("Évolution de la valeur totale en €")
    line_chart(df_value)

    # 3) Slider pour sélectionner un timestamp
    st.subheader("Sélection du timestamp pour le camembert")
    timestamps = df_value['timestamp'].tolist()
    selected_ts = st.select_slider(
        "Choisissez une heure", 
        options=timestamps, 
        value=timestamps[0]
    )

    # 4) Filtrer les assets pour ce timestamp et afficher le camembert
    df_sel = df[df['timestamp'] == selected_ts]
    st.subheader(f"Répartition des assets au {selected_ts.strftime('%Y-%m-%d %H')}h")
    pie_chart(df_sel)

    # 5) (Optionnel) Afficher la table filtrée
    st.write(df_sel)

if __name__ == "__main__":
    main()
