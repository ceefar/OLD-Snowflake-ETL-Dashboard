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

    # SIDEBAR portfolio/developer mode toggle
    with st.sidebar:
        dev_mode = st.checkbox(label="Portfolio Mode")


    # HEADER section
    topcol1, topcol2 = st.columns([1,5])
    topcol2.markdown("## Your Cafe App Dashboard")
    try:
        topcol1.image("imgs/cafe_sign.png")
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

        with topMetricSelectCol2:
            selected_stores = st.multiselect(label='What Stores Would You Like Info On?', default=['All'],
                        options=['Uppingham', 'Longridge', 'Chesterfield', 'London Camden', 'London Soho', 'All', 'Only London', 'Only Outside London'])

            stores_query_selector = {"Only London":"AND store_name = 'London Camden' OR store_name = 'London Soho'", 
                                    'Only Outside London':"AND store_name = 'Uppingham' OR store_name = 'Longridge' OR store_name = 'Chesterfield'",
                                    'All':"AND store_name = 'Uppingham' OR store_name = 'Longridge' OR store_name = 'Chesterfield' OR store_name = 'London Camden' OR store_name = 'London Soho'",
                                    'Uppingham':"AND store_name = 'Uppingham'", 'Longridge':"AND store_name = 'Longridge'", 'Chesterfield':"AND store_name = 'Chesterfield'",
                                    'London Camden':"AND store_name = 'London Camden'", 'London Soho':"AND store_name = 'London Soho'"}

            # switch case to create the final part of the store select query, kinda has to be done this way
            # since you could accidentally select something like "Only London" + "Chesterfield", in which case "Only" is the override,
            # with all still having the highest precedent, and being set (to all) if nothing is included, could have been done another way but i like this
            if len(selected_stores) == 1:
                final_stores = stores_query_selector[selected_stores[0]]
            elif len(selected_stores) == 0:
                final_stores = stores_query_selector["All"]
            elif "All" in selected_stores:
                final_stores = stores_query_selector["All"]
            elif "Only London" in selected_stores:
                final_stores = stores_query_selector["Only London"]
            elif "Only Outside London" in selected_stores:
                final_stores = stores_query_selector["Only Outside London"]
            else:
                # join them all, map is needed as lambda applies apostrophes around each item in the iterable e.g. 'London Soho'
                # obvs if all, only london, and only outside london are removed this is how the query would be created, in one line, clean af
                final_stores = "AND store_name = " + " OR store_name = ".join(map((lambda a: f"'{a}'"), selected_stores))
            
        st.write("##")

    # METRIC container
    with st.container():
        
        # for display, create a display string unless the query has length that is the max length (for the query), which means it's "All"
        # done because we dont want "Uppingham or Longridge or Chesterfield or..."
        selected_stores_display = final_stores.replace("'","").replace("OR store_name =","or")[16:] if len(final_stores) < 149 else "All"
        st.markdown(f"""###### :calendar: Selected Date : {dateme} """)
        st.markdown(f"""###### :coffee: Selected Stores : {selected_stores_display} """)
        st.write("##")

        # ---- for st.metric header widget ----
        col1, col2, col3, col4 = st.columns(4)
        with st.expander("See The Queries"):
            with st.echo():
                metricVals = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                        SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{dateme}' {final_stores};")

                day_before = run_query(f"SELECT DATE(DATEADD(day, -1,'{dateme}'))")
                day_before = day_before[0][0]

                metricDeltas = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                        SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{day_before}' {final_stores};")

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


