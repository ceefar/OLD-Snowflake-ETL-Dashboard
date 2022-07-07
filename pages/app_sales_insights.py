# app_sales_insights.py

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


# ---- db functions ----

def db_get_cups_sold_by_hour_one_store(store_name, current_day):
    """ write me """
    cups_sold = db.get_cups_sold_by_hour_one_store(store_name, current_day)
    return(cups_sold[0][0])


def run():

    # BASE QUERIES queries
    currentdate = db.get_basic_dates("current")

    # CHART NEW TEST hour and user input
    # NEEDS TO BE CACHED!
    with st.container():
        st.write(f"#### Stores Sales Insights dayname_daynumb_string - By Hour Of The Day") # time of day popularity or sumnt?
        st.write("Try to reduce overhead (staff hours) during prolonged quieter periods for huge savings")
        st.write("##")

        stores_list = ['Uppingham', 'Longridge', 'Chesterfield', 'London Camden', 'London Soho']
        store_selector = st.selectbox("Choose The Store", options=stores_list, index=0)


        

        hour_cups_data = db.get_cups_sold_by_hour_one_store(store_name=store_selector, current_day=db.get_basic_dates("first"))
        st.write("##")
        # cups, hour, name
        #print(f"{hour_cups_data = }")
        just_names_list = []
        just_hour_list = []
        just_cupcount_list = []
        for cups_data in hour_cups_data:
            just_cupcount_list.append(cups_data[0])
            just_hour_list.append(cups_data[1])
            just_names_list.append(cups_data[2])
        
        source4 = pd.DataFrame({
        "DrinkName": just_names_list,
        "CupsSold":  just_cupcount_list,
        "HourOfDay": just_hour_list
        })

        bar_chart4 = alt.Chart(source4).mark_bar().encode(
            color="DrinkName:N", # x="month(Date):O",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300, width=1000)

        text4 = alt.Chart(source4).mark_text(dx=-15, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        st.altair_chart(bar_chart4 + text4, use_container_width=True)

        st.write("##")
        st.write("---")


run()