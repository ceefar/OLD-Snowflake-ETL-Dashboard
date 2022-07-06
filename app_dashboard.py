# app_dashboard.py
import streamlit as st
import snowflake.connector

# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"], ocsp_fail_open=False)

conn = init_connection()

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def run():
    st.write("Let gooooo")

    
    # METRIC container
    with st.container():

  
        st.markdown(f"""#### :calendar: Snapshot For 05/07 """)
        st.write("##")
        # ---- for st.metric header widget ----
        col1, col2, col3, col4 = st.columns(4)

        tempmetric = run_query("SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '2022-07-05';")

        print(f"{tempmetric = }")

        tempmetric1 = float(tempmetric[0][0])
        tempmetric2 = float(tempmetric[0][1])
        tempmetric3 = tempmetric[0][2]
        tempmetric4 = tempmetric[0][3]

        print(f"{tempmetric1 = }")
        print(f"{tempmetric2 = }")
        print(f"{tempmetric3 = }")
        print(f"{tempmetric4 = }")

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