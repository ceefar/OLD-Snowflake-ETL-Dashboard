# app_store_menus.py

# ---- imports ----

# for web app 
import streamlit as st
import streamlit.components.v1 as stc
# for charts, dataframes, data manipulation
import altair as alt
import pandas as pd
# for date time objects
import datetime
# for db integration
import db_integration as db 


# ---- db connection ----

# connection now started and passed around from db_integration once using singleton
conn = db.init_connection()

# perform get/fetch query - uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    """ self referencing """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


# FIXME
# NOTE 
################### MIGHT NOT NEED ###################

# ---- main web app ----

with st.sidebar:
    st.write("##")
    st.markdown("#### Portfolio Mode")
    st.write("To view live code snippets")
    devmode = st.checkbox("Portfolio Mode")
    st.write("##")
    st.markdown("#### Advanced Mode")
    st.write("For more advanced query options")
    advanced_options_1 = st.checkbox("Advanced Mode") 


def run():

    # BASE QUERIES queries
    currentdate = run_query("SELECT DATE(GETDATE())")
    yesterdate = run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))")
    firstdate = run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")
    currentdate = currentdate[0][0]
    yesterdate = yesterdate[0][0]
    firstdate = firstdate[0][0]

    # ALTAIR CHART item type sold by hour of day
    with st.container():
        st.write(f"### :bulb: Insight - Sales vs Time of Day") 
        st.write("##### AKA Popularity")
        st.write("Includes everything except the 3 most popular items") # because they are all favoured so really theres 15 not 3
        st.write("##")

run()