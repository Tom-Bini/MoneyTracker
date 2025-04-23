import streamlit as st
import sqlite3
from datetime import datetime

class App:
    def __init__(self):
        self.run()

    def run(self):
        st.write("Hello, World!")

        st.line_chart()

    @st.cache_resource
    def get_connection():
        conn = sqlite3.connect("money_tracker.db", check_same_thread=False)
        return conn

if __name__ == "__main__":
    App()