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

    # 3) Graphique d'évolution de la répartition par type (en pourcentage)
    st.subheader("Évolution de la répartition des assets par type (%)")
    
    # Préparer les données pour le graphique en aires empilées
    df_stacked = (
        df
        .groupby(['timestamp', 'type'])['value_in_EUR']
        .sum()
        .reset_index()
        .pivot(index='timestamp', columns='type', values='value_in_EUR')
        .fillna(0)  # Remplacer les NaN par 0
    )
    
    # Calculer les pourcentages pour chaque timestamp
    df_percentage = df_stacked.div(df_stacked.sum(axis=1), axis=0) * 100
    df_percentage = df_percentage.reset_index()
    
    # Convertir en format long pour Plotly
    df_melted = df_percentage.melt(
        id_vars=['timestamp'], 
        var_name='type', 
        value_name='percentage'
    )
    
    # Créer le graphique en aires empilées avec pourcentages
    fig = px.area(
        df_melted,
        x='timestamp',
        y='percentage',
        color='type',
        title="Évolution de la répartition des assets par type (%)",
        color_discrete_map={'Bitcoin': '#F4B401','Altcoin':'#26A96C','DeFi':'#2BC016','Fiat':'#387D7A'}
    )
    
    # Améliorer l'affichage
    fig.update_layout(
        xaxis_title="Temps",
        yaxis_title="Pourcentage (%)",
        yaxis=dict(range=[0, 100]),  # Fixer l'axe Y entre 0 et 100%
        hovermode='x unified'
    )
    
    # Personnaliser le format du hover
    fig.update_traces(hovertemplate='%{y:.1f}%<extra></extra>')
    
    st.plotly_chart(fig)

    # 4) (Optionnel) Afficher un aperçu des données récentes
    st.subheader("Aperçu des données récentes")
    latest_timestamp = df['timestamp'].max()
    df_latest = df[df['timestamp'] == latest_timestamp]
    st.write(f"Données pour {latest_timestamp.strftime('%Y-%m-%d %H')}h :")
    st.write(df_latest)

if __name__ == "__main__":
    main()