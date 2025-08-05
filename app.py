import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

DB_PATH = "poids_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM poids", conn)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    conn.close()
    return df

def insert_data(date, poids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO poids (Date, Poids) VALUES (?, ?)", (date, poids))
    conn.commit()
    conn.close()

def compute_weekly_means(df):
    df["Semaine"] = df["Date"].dt.to_period("W").apply(lambda r: r.start_time)
    return df.groupby("Semaine")["Poids"].mean().reset_index()

def compute_rolling_mean(df, window=7):
    df = df.set_index("Date").sort_index()
    df["Moyenne Glissante"] = df["Poids"].rolling(window=window).mean()
    return df.reset_index()

def add_target_line(start_date, end_date, start_weight, end_weight):
    dates = pd.date_range(start=start_date, end=end_date)
    slope = (end_weight - start_weight) / (len(dates) - 1)
    values = [start_weight + i * slope for i in range(len(dates))]
    return pd.DataFrame({"Date": dates, "Objectif": values})

st.title("Suivi de Poids 🧭")

df = init_db()

# Ajouter une nouvelle entrée
with st.form("ajout_poids"):
    date_input = st.date_input("Date", value=datetime.today())
    poids_input = st.number_input("Poids (kg)", min_value=30.0, max_value=200.0, step=0.1)
    submitted = st.form_submit_button("Ajouter")
    if submitted:
        insert_data(date_input.strftime("%Y-%m-%d"), poids_input)
        st.success("Poids ajouté avec succès !")
        st.experimental_rerun()

# Rafraîchir les données
df = init_db()

# Moyenne fixe (hebdo)
weekly_means = compute_weekly_means(df)

# Moyenne glissante
rolling_df = compute_rolling_mean(df)

# Droite de tendance
x = np.arange(len(df))
coeffs = np.polyfit(x, df["Poids"], 1)
trend = coeffs[0] * x + coeffs[1]

# Objectif de poids
target_df = add_target_line("2025-02-07", "2025-09-01", 85.5, 70)

# Tracé
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Date"], df["Poids"], label="Poids quotidien", marker="o", markersize=3)
ax.plot(weekly_means["Semaine"], weekly_means["Poids"], label="Moyenne hebdo", linestyle="--")
ax.plot(rolling_df["Date"], rolling_df["Moyenne Glissante"], label="Moyenne glissante 7j")
ax.plot(df["Date"], trend, label="Tendance", linestyle=":")
ax.plot(target_df["Date"], target_df["Objectif"], label="Objectif", linestyle="-.")

ax.set_xlabel("Date")
ax.set_ylabel("Poids (kg)")
ax.set_title("Évolution du poids")
ax.legend()
ax.grid(True)
st.pyplot(fig)
