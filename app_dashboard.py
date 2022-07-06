# app_dashboard.py

# ---- imports ----
# for web app 
import streamlit as st
import snowflake.connector
# for date time objects
import datetime # from datetime import datetime


# ---- snowflake db setup ----
# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"], ocsp_fail_open=False)

conn = init_connection()


# ---- functions ----
# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


# ---- main web app ----
def run():

    # DATE SELECTER container
    with st.container():
        
        currentdate = run_query("SELECT DATE(GETDATE())")
        yesterdate = run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))")
        firstdate = run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")
        currentdate = currentdate[0][0]
        yesterdate = yesterdate[0][0]
        firstdate = firstdate[0][0]

        dateme = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate)        

    # METRIC container
    with st.container():

        st.markdown(f"""#### :calendar: Snapshot For {dateme} """)
        st.markdown(f"**Today is {currentdate}** (data available in x hours)") # TODO - would be sooo dope, even if its by hour (obvs never seconds)
        st.write("##")
        # ---- for st.metric header widget ----
        col1, col2, col3, col4 = st.columns(4)

        tempmetric = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{dateme}';")

        try:
            tempmetric1 = float(tempmetric[0][0])
        except TypeError:
            tempmetric1 = 0

        try:
            tempmetric2 = float(tempmetric[0][1])
        except TypeError:
            tempmetric2 = 0
        
        try:    
            tempmetric3 = tempmetric[0][2]
        except TypeError:
            tempmetric3 = 0

        try:
            tempmetric4 = tempmetric[0][3]
        except TypeError:
            tempmetric4 = 0

        # note delta can be can be off, normal, or inverse
        col1.metric(label="Total Revenue", value=f"${tempmetric1:.2f}", delta=f"{1:.2f}", delta_color="normal")
        col2.metric(label="Avg Spend", value=f"${tempmetric2:.2f}", delta=f"{1:.2f}", delta_color="normal")
        col3.metric(label="Total Customers", value=tempmetric3, delta=0, delta_color="off") 
        col4.metric(label="Total Coffees Sold", value=tempmetric4, delta=0, delta_color="off")

        st.write("---")


    st.write("##")
    #rows = run_query("SELECT * from redshift_customerdata;")

    # Print results.
    #for row in rows:
    #   st.write(f"{row[0]} has a :{row[1]}:")
    #   print(row)

    #print(rows)

run()