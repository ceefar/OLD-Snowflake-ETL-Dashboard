# app_dashboard.py

# ---- imports ----
# for web app 
import streamlit as st
import snowflake.connector
import streamlit.components.v1 as stc
# for date time objects
import datetime # from datetime import datetime


# ---- snowflake db setup ----
# Initialize connection - uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"], ocsp_fail_open=False)

conn = init_connection()


# ---- functions ----
# Perform get/fetch query - uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    """ ig with memo what they want you to do is pull all the data and just manipulate with python but meh """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def split_metric_eafp(results, vals_or_delta):
    """ creates list of query results for the metric values and delta, saves doing a massive switch case since try excepts are needed to set either value or 0 """
    delta_result = []
    values_result = []
    # loop the given list from the query and place it into a new list while performing try except to set either its value or 0 
    for value in results:
        try:
            # if has data in value[i] (which is metricVals/delta[0][i]), set it to list outside of loop to return on complete
            if vals_or_delta == "delta":
                delta_result.append(value)
            else:
                values_result.append(value)
        except TypeError:
            # if no data will throw type error, if so set to 0 (so it isn't displayed in the metric, or is clear there is no data)
            if vals_or_delta == "delta":
                delta_result.append(0)
            else:
                values_result.append(0)
    # return the results
    if vals_or_delta == "delta":
        return(delta_result)
    else:
        return(values_result)


# ---- main web app ----
def run():

    # BASE QUERIES queries
    currentdate = run_query("SELECT DATE(GETDATE())")
    yesterdate = run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))")
    firstdate = run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")
    currentdate = currentdate[0][0]
    yesterdate = yesterdate[0][0]
    firstdate = firstdate[0][0]


    # HEADER section
    topcol1, topcol2 = st.columns([1,5])
    topcol2.markdown("## Your Cafe App Dashboard")
    try:
        topcol1.image("imgs\cafe_sign.png")
    except:
        st.write("")
    st.write("##")
    st.write("---")


    # DATE SELECTER container
    with st.container():

        st.markdown("#### Daily Snapshot")
        topMetricSelectCol1, topMetricSelectCol2 = st.columns(2)
        with topMetricSelectCol1:
            dateme = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate)        
        st.write("##")

    # METRIC container
    with st.container():

        st.markdown(f"""###### :calendar: Selected Date : {dateme} """)
        st.markdown("""###### :coffee: Selected Stores : All """)
        st.write("##")
        # ---- for st.metric header widget ----
        col1, col2, col3, col4 = st.columns(4)

        metricVals = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{dateme}';")

        day_before = run_query(f"SELECT DATE(DATEADD(day,-1,'{dateme}'))")
        day_before = day_before[0][0]

        metricDeltas = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{day_before}';")

        # get result from queries partially selected by user but apply try except (eafp) as if there is no result returned we want the result to become 0 (not None)                
        metricDeltaResults = split_metric_eafp(metricDeltas[0], "delta")
        metricValueResults = split_metric_eafp(metricVals[0], "vals")

        # unpack the list from eafp function and set its own values for the metric (setting as easier for creating delta, plus can use in other places if needed)
        metric_tot_rev_val, metric_avg_spend_val, metric_tot_cust_val, metric_tot_cofs_val = float(metricValueResults[0]), float(metricValueResults[1]), metricValueResults[2], metricValueResults[3]
        # delta values are the current day minus the previous day hence why setting above vars through unpacking instead of adding directly to below metric
        metric_tot_rev_delta, metric_avg_spend_delta, metric_tot_cust_delta, metric_tot_cofs_delta = (metric_tot_rev_val - float(metricDeltaResults[0])), (metric_avg_spend_val - float(metricDeltaResults[1])), (metric_tot_cust_val - metricDeltaResults[2]), (metric_tot_cofs_val - metricDeltaResults[3])

        # note delta can be can be off, normal, or inverse (delta = current days value - previous days value)
        col1.metric(label="Total Revenue", value=f"${metric_tot_rev_val:.2f}", delta=f"${metric_tot_rev_delta:.2f}", delta_color="normal")
        col2.metric(label="Avg Spend", value=f"${metric_avg_spend_val:.2f}", delta=f"${metric_avg_spend_delta:.2f}", delta_color="normal")
        col3.metric(label="Total Customers", value=metric_tot_cust_val, delta=metric_tot_cust_delta, delta_color="normal") 
        col4.metric(label="Total Coffees Sold", value=metric_tot_cofs_val, delta=metric_tot_cofs_delta, delta_color="normal")

        st.write("---")

    st.write("##")

    # rows = run_query("SELECT * from redshift_customerdata;")

    # Print results.
    # for row in rows:
    #    st.write(f"{row[0]} has a :{row[1]}:")
    #    print(row)

    # print(rows)

run()


