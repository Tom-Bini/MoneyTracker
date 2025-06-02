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

# Configuration des monnaies
CURRENCIES = {
    'EUR': {'column': 'value_in_EUR', 'symbol': '€', 'total_column': 'total_value_in_EUR'},
    'USD': {'column': 'value_in_USD', 'symbol': '$', 'total_column': 'total_value_in_USD'},
    'BTC': {'column': 'value_in_BTC', 'symbol': '₿', 'total_column': 'total_value_in_BTC'}
}

# Fonction pour afficher le graphique camembert (toujours en EUR)
def pie_chart(df):
    grouped = df.groupby('type').agg({'value_in_EUR':'sum'}).reset_index()
    fig = px.pie(
        grouped, 
        names='type', 
        values='value_in_EUR', 
        title="Répartition des assets par type",
        color='type',
        color_discrete_map={'Bitcoin': '#F4B401','Altcoin':'#26A96C','DeFi':'#2BC016','Fiat':'#387D7A'}
    )
    st.plotly_chart(fig)

# Fonction pour afficher le graphique de la valeur totale
def line_chart(df, currency):
    currency_info = CURRENCIES[currency]
    fig = px.line(
        df, 
        x='timestamp', 
        y=currency_info['total_column'], 
        title=f"Évolution de la valeur totale en {currency} ({currency_info['symbol']})"
    )
    st.plotly_chart(fig)

def main():
    st.title("Money Tracker Dashboard")
    
    # Sélecteur de monnaie en haut de la page
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_currency = st.selectbox(
            "Choisissez la monnaie :",
            options=list(CURRENCIES.keys()),
            index=0  # EUR par défaut
        )
    
    currency_info = CURRENCIES[selected_currency]

    # 1) On charge tous les assets récents
    df = get_data("SELECT * FROM assets WHERE timestamp >= '2025-01-01'")

    # On convertit la colonne timestamp en datetime (format "YYYY-MM-DD HH")
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H")

    # 2) Graphique de l'évolution
    # On agrège pour la line chart selon la monnaie sélectionnée
    df_value = (
        df
        .groupby('timestamp')[currency_info['column']]
        .sum()
        .reset_index(name=currency_info['total_column'])
        .sort_values('timestamp')
    )

    st.subheader(f"Évolution de la valeur totale en {selected_currency}")
    line_chart(df_value, selected_currency)

    # 3) Slider pour sélectionner un timestamp
    st.subheader("Sélection du timestamp pour le camembert")
    timestamps = df_value['timestamp'].tolist()
    selected_ts = st.select_slider(
        "Choisissez une heure", 
        options=timestamps, 
        value=timestamps[0] if timestamps else datetime.now()
    )

    # 4) Filtrer les assets pour ce timestamp et afficher le camembert
    df_sel = df[df['timestamp'] == selected_ts]
    st.subheader(f"Répartition des assets au {selected_ts.strftime('%Y-%m-%d %H')}h")
    pie_chart(df_sel)

    # 5) (Optionnel) Afficher la table filtrée
    if not df_sel.empty:
        st.write(df_sel)
    else:
        st.write("Aucune donnée disponible pour ce timestamp.")

if __name__ == "__main__":
    main()