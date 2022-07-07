# db_integration.py

# ---- imports ----

# for web app 
import streamlit as st
import snowflake.connector
# for datetime objects
import datetime


# ---- snowflake db setup ----

# initialize connection - uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(**st.secrets["snowflake"])

conn = init_connection()

# perform get/fetch query - uses st.experimental_memo to only rerun when the query changes or after 10 min.
# ig with memo what they want you to do is pull all the data and just manipulate with python but meh
@st.experimental_memo(ttl=600)
def run_query(query):
    """ write me """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


# ---- query functions ----

def get_basic_dates(return_date:str) -> datetime: # actually returns datetime.date but might refactor
    """ 
    get current date, yesterdays date, the first date with valid data in the db
    """
    # big fan of using dictionaries for switch cases if you can't tell, this grabs the query based on the given passed parameter (e.g. current)
    what_date_dict = {"current":run_query("SELECT DATE(GETDATE())"), "yesterday":run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))"),
                        "first":run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")}

    # if return date in dict do return else return sumnt else
    if return_date in what_date_dict:
        # run query from the dictionary based on given parameter, then unpack the result (as is nested (list(tuple(result))) as is a solo query)
        select_return_date = what_date_dict[return_date][0][0]
        return(select_return_date)
    else:
        return(None)


def get_day_before(set_date:datetime) -> datetime:
    """ returns the date before the given date, takes datetime (maybe also takes a string) """
    day_before = run_query(f"SELECT DATE(DATEADD(day, -1,'{set_date}'))")
    # unpack the query before sending
    return(day_before[0][0])


def get_cups_sold_by_hour_one_store(store_name, current_day) -> tuple:
    """ write me """
    print(f"{store_name = }")
    print(f"{current_day = }")
    cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour, i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE store = '{store_name}' AND DATE(d.timestamp) = '{current_day}' GROUP BY d.timestamp, i.item_name"
    cups_by_hour = run_query(cups_by_hour_query)
    print(cups_by_hour)
    return(cups_by_hour)


