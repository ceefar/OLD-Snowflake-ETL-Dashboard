# app_sales_insights.py

# ---- notes ----

# 1. manually adheres to pep8 as best possible, no linter used as trying to learn pep8 styling as much as possible as a jnr dev (syling is important mkay)
# 1b. but kinda rip pep8 because parts are messy (e.g. excessively long lines) but is entirely due to portfolio/dev mode display needs 
# 2. as per 1b, there is some repeated code but entirely due to porfolio + the way echo works (method which runs & displays live code on the web app @ the same time)
# 3. due to weird cffi module issues must be built with python version 3.7 (not 3.9 where it was developed), important for pushing to streamlit cloud for web app
# 4. entirely done by me for my group project, streamlit was not included in any of our lessons I just think its a great too and works perf with snowflake
#       - others will be using grafana or metabase, though clean doesn't allow for dynamic user selections, multipage dashboard web app
#       - i feel this not only shows my drive to go above and beyond to wow the end user, but also my ability to independently learn new frameworks   
# 5. comments are excessive for portfolio mode, i am a big comment enjoyer but normally would not comment so extensively, particularly where code is self-referencing 


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


# ---- main web app ----

with st.sidebar:
    st.write("##")
    st.markdown("#### Portfolio Mode")
    st.write("To view live code snippets")
    devmode = st.checkbox("Portfolio Mode", key="devmode-insights")
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
        st.write("##")

        stores_list = ['Chesterfield', 'Uppingham', 'Longridge',  'London Camden', 'London Soho']
        altairChartSelectCol1, altairChartSelectCol2 = st.columns(2)
        with altairChartSelectCol1:
            current_day = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate)  
        with altairChartSelectCol2:
            store_selector = st.selectbox("Choose The Store", options=stores_list, index=0) 

        # PORTFOLIO 
        # ADD FUCKING COMMENTS && EXPANDER && PORTFOLIO MODE CHECKBOX TO SIDEBAR 
        if devmode:
            with st.expander("Complex 'Join/Group By' SQL Query (converted from original complex MySQL Query)"):       
                with st.echo():
                    # note - data hosted on redshift, moved to s3 bucket, then transferred to snowflake warehouse
                    # inner join data and items tables on matching transaction ids, for each store, at set dates for each item
                    cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                        i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                                        WHERE store = '{store_selector}' AND DATE(d.timestamp) = '{current_day}' GROUP BY d.timestamp, i.item_name"
                    hour_cups_data = run_query(cups_by_hour_query)
        else:
            cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                                WHERE store = '{store_selector}' AND DATE(d.timestamp) = '{current_day}' GROUP BY d.timestamp, i.item_name"
            hour_cups_data = run_query(cups_by_hour_query)

        st.write("##")
        
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
        ).properties(height=300)

        text4 = alt.Chart(source4).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        # ---- end altair table creation ----
        # note hasn't been initialised yet tho


        # ---- start new insights calculation ----

        # BIG N0TE!
        #   - 100 need try except incase hour data is missing or all data is missing btw
 

        # FIXME 
        # TODO 
        # PORTFOLIO - PUT THIS SHIT IN ECHO, MANS IS A GOATPANDA NOW... jesus i need to sleep XD
        # get unique values in HourOfDay column to loop (returns array object so convert to list), then sort/order it
        uniqueCols = sorted(list(source4['HourOfDay'].unique()))

        results_dict = {}
        # get sum of cupsSold column based on condition (HourOfDay == x), added to dictionary with key = hour, value = sum of cups sold for hour
        for value in uniqueCols:
            cupForHour = source4.loc[source4['HourOfDay'] == value, 'CupsSold'].sum()
            results_dict[value] = cupForHour

        try:
            average_hourcups = sum(results_dict.values()) / len(results_dict.values())
        except ZeroDivisionError:
            average_hourcups = 0

        # create a new dictionary from hour/cups dictionary but sorted
        sort_by_value = dict(sorted(results_dict.items(), key=lambda x: x[1]))   
        # create a list of formatted strings with times and cups sold including am or pm based on the time
        sort_by_value_formatted_list = list(map(lambda x: (f"{x[0]}pm [{x[1]} cups sold]") if x[0] > 11 else (f"{x[0]}am [{x[1]} cups sold]"), sort_by_value.items()))
        

        try:
            # list the keys (times, ordered) only, slice the first and last elements in the array (list) [start:stop:step]
            worst_time, best_time = list(sort_by_value.keys())[::len(sort_by_value.keys())-1]
            worst_performer, best_performer = sort_by_value_formatted_list[::len(sort_by_value_formatted_list)-1]
        except ValueError:
            worst_time, best_time, worst_performer, best_performer = 0,0,0,0

        # TO ADD HERE
        # print(f"{average_hourcups = }") # HOURS UNDER THIS TIME COULD POSSIBLY BENEFIT FROM AN OFFER, HOURS ABOVE IS STAFF
        # AVG SPECIFICS
        # GRANULAR TO ACTUAL PRODUCTS [SKIPPING FOR NOW] 
        # HOW MUCH IT OVERPERFORMED BY IG [SKIPPING FOR NOW]
        # ECHO & PORTFOLIO MODE

        above_avg_hourcups = {}
        for hour, cups in results_dict.items():
                if cups >= average_hourcups:
                    above_avg_hourcups[hour] = cups

        # RN JUST MOVE TO ADVANCED MODE!
        # PLS DO 1 ACTION LATER!

        # end insights calc

        
        METRIC_ERROR_MSG = """
            Wild MISSINGNO Appeared!\n
            No Data for {} on {}\n
            ({})
            """

        INSIGHT_TIP_1 = f"""
            ###### Store Insights\n
            Your personal insights dynamically created from the data you've selected\n
            ###### Worst Performing Hour : {worst_performer}\n
            At {worst_time}{f"{'pm' if worst_time > 11 else 'am'}"} consider offers + less staff\n
            ###### Best Performing Hour: {best_performer}\n
            At {best_time}{f"{'pm' if best_time > 11 else 'am'}"} ensure staff numbers with strong workers at this time to maximise sales\n
            ###### Sales Analysis\n
            Average Sales Per Hour: {average_hourcups:.0f} cups sold\n
            Hours Above Average Sales: {", ".join(list(map(lambda x : f"{x}pm" if x > 11 else f"{x}am" , list(above_avg_hourcups.keys()))))} 
            """

        # if no data returned for store and day then show missingno (missing number) error
        if hour_cups_data:
            st.altair_chart(bar_chart4 + text4, use_container_width=True)
            with st.expander("Gain Insight"):
                insightCol1, insightCol2 = st.columns([1,5])
                insightCol2.success(INSIGHT_TIP_1)
                insightCol1.image("imgs/insight.png")  # width=140
                # formatting for img if its a london store
                current_store = str(store_selector).lower()
                if "london" in current_store:
                    current_store = "-".join(current_store)
                insightCol1.image(f"imgs/cshop-small-{current_store}.png") # width=140
        else:
            _, altairChartCol1, altairChartCol2 = st.columns([1,3,2])
            try:
                altairChartCol2.image("imgs/Missingno.png")
            except FileNotFoundError:
                pass
            altairChartCol1.error(METRIC_ERROR_MSG.format(store_selector, current_day, "no selected or previous day available"))
            st.write("##")
            st.sidebar.info("Cause... Missing Numbers... Get it...")

        st.write("##")
        st.write("##")
        st.write("---")



    # ---- NEW SECTION ----

    # ALTAIR CHART product sold by hour of day (COMPARE 2?!) - INDIVIDUAL ITEM VERSION OF ABOVE
    with st.container():
        st.write(f"### :bulb: Insight - Compare Two Items") 

        compare1StoreCol, compare1DayCol = st.columns(2)

        # new store selector
        with compare1StoreCol:
            store_selector_2 = st.selectbox(label="Choose The Store", key="store_select_2", options=stores_list, index=0) 
        
        # new date selector
        with compare1DayCol:
            current_day_2 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate, key="day_select_2")  

        # get only main item name
        get_main_item = run_query(f"SELECT DISTINCT i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}'")
        final_main_item_list = []
        for item in get_main_item:
            final_main_item_list.append(item[0])

        # select any item from the store for comparison
        item1Col, itemInfoCol, item2Col = st.columns([2,1,2])
        with item1Col:
            item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_2}", key="item_selector_1", options=final_main_item_list, index=0) 
        with item2Col:
            item_selector_2 = st.selectbox(label=f"Choose An Item From Store {store_selector_2}", key="item_selector_2", options=final_main_item_list, index=1)
        with itemInfoCol:
            st.write("##")
            if advanced_options_1:
                st.info("Advanced Mode : On")
            else:
                st.warning("Try Advanced Mode!")



        # ---- new [testing] - advanced mode ----
        
        st.write("##")

        if advanced_options_1:
            # left (item 1) col
            with item1Col:
                item_flavours_1 = run_query(f"SELECT DISTINCT i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}' AND i.item_name = '{item_selector_1}';")
                final_item_flavours_list = []
                dont_print_2 = [final_item_flavours_list.append(flavour[0]) for flavour in item_flavours_1]
                # flav_selector_1 = st.selectbox(label=f"Choose A Flavour For {item_selector_1}", key="flav_selector_1", options=final_item_flavours_list, index=0)  
                multi_flav_selector_1 = st.multiselect(label=f"Choose A Flavour For {item_selector_1}", key="multi_flav_select_1", options=final_item_flavours_list, default=final_item_flavours_list[0])
                # size_selector_1 = st.selectbox(label=f"Choose A Size For {item_selector_1}", key="size_selector_1", options=["Regular","Large"], index=0)
                multi_size_selector_1 = st.multiselect(label=f"Choose A Size For {item_selector_1}", key="multi_size_select_1", options=["Regular","Large"], default="Regular")
            
                if not devmode:

                    flavour_1_is_null = False

                    # split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                    if len(multi_flav_selector_1) == 1:
                        if multi_flav_selector_1[0] is None:
                            final_flav_select_1 = f"i.item_flavour is NULL"
                            flavour_1_is_null = True
                        else:
                            final_flav_select_1 = f"i.item_flavour='{multi_flav_selector_1[0]}'"
                    
                    # else more than 1 selection, so dynamically join items
                    elif len(multi_flav_selector_1) > 1:
                        final_flav_select_1 = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_1)))
                        final_flav_select_1 = "(i.item_flavour=" + final_flav_select_1 + ")"

                    # else if no flavour was selected (any valid flavour was removed from the multiselect box by the user) then 2 cases to deal with      
                    elif len(multi_flav_selector_1) == 0:
                        final_flav_select_1 = f"i.item_flavour='{final_item_flavours_list[0]}'"
                        if multi_flav_selector_1[0] is None:
                            final_flav_select_1 = f"i.item_flavour is NULL"
                        else:                
                            final_flav_select_1 = f"i.item_flavour='{final_item_flavours_list[0]}'"
                            itemInfoCol.error(f"< Flavour = {final_item_flavours_list[0]}")

                    # split size selector if multi select, only ever Regular or Large so easier to do
                    if len(multi_size_selector_1) == 1:
                        final_size_select_1 = f"i.item_size='{multi_size_selector_1[0]}'"
                    elif len(multi_size_selector_1) == 0:
                        final_size_select_1 = "i.item_size='Regular'"
                        itemInfoCol.error(f"< Size defaults to Regular")
                    else:
                        final_size_select_1 = f"(i.item_size='{multi_size_selector_1[0]}' OR i.item_size = '{multi_size_selector_1[1]}')"

                
            # right (item 2) col
            # the advanced select for item 2 runs regardless of devmode here as dev mode only needs to show one case (since they are both the same code)
            with item2Col:
                 # ---- user select ----

                # get list (well actually tuples) of flavours for the user selected item from the database
                item_flavours_2 = run_query(f"SELECT DISTINCT i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}' AND i.item_name = '{item_selector_2}';")
                final_item_flavours_list_2 = []
                # convert the returned tuples into a list (don't print required as streamlit prints (to web app) list comprehensions that aren't assigned to variables)
                dont_print_3 = [final_item_flavours_list_2.append(flavour[0]) for flavour in item_flavours_2]
                # flav_selector_2 = st.selectbox(label=f"Choose A Flavour For {item_selector_2}", key="flav_selector_2", options=final_item_flavours_list, index=0)  
                multi_flav_selector_2 = st.multiselect(label=f"Choose A Flavour For {item_selector_2}", key="multi_flav_select_2", options=final_item_flavours_list_2, default=final_item_flavours_list_2[0])
                # size_selector_2 = st.selectbox(label=f"Choose A Size For {item_selector_2}", key="size_selector_2", options=["Regular","Large"], index=0)
                multi_size_selector_2 = st.multiselect(label=f"Choose A Size For {item_selector_2}", key="multi_size_select_2", options=["Regular","Large"], default="Regular")

                # ---- flavour query creation ----

                # ---- important ----
                # required boolean flag for slightly altering the sql query (flavour is the only case with Null values so simple boolean flag is fine)
                # if flavour is Null/None then we need to tweek the initial SELECT to get the correct (unique) item name
                flavour_2_is_null = False

                # split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                # only required for flavour, as size can only be regular or large
                # if only 1 flavour then 2 cases to deal with
                if len(multi_flav_selector_2) == 1:
                    # check if this item has flavours by checking what was returned by the database for this item
                    if multi_flav_selector_2[0] is None:
                        # if there is no flavour for this then set the query to validate on NULL values (no = operator, no '')
                        final_flav_select_2 = f"i.item_flavour is NULL"
                        # also set null flavour flag to True so that final sql can be altered to output valid string (i.item_name, i.item_size, i.item_flavour) 
                        flavour_2_is_null = True
                    else:
                        # else just 1 valid flavour was selected so create standard query
                        final_flav_select_2 = f"i.item_flavour='{multi_flav_selector_2[0]}'"

                # else if more than 1 flavour was selected then we must dynamically join them together so the query include OR statements
                elif len(multi_flav_selector_2) > 1:
                    final_flav_select_2 = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_2)))
                    final_flav_select_2 = "(i.item_flavour=" + final_flav_select_2 + ")"

                # else if no flavour was selected (any valid flavour was removed from the multiselect box by the user) then 2 cases to deal with  
                elif len(multi_flav_selector_2) == 0:
                    # first check the available flavours that were returned by the database for this item, if true user has removed the 'None' flavour option from multiselect
                    if multi_flav_selector_2[0] is None:
                        # if there is no flavour then set to validate on NULL
                        final_flav_select_2 = f"i.item_flavour is NULL"
                    else:      
                        # else (if the first flavour select option isn't None) then it means the user removed all from valid flavours from multiselect                
                        final_flav_select_2 = f"i.item_flavour='{final_item_flavours_list_2[0]}'"
                        # so add the 'default', aka first item in the flavours list, to the query and inform the user of what has happened
                        itemInfoCol.error(f"Flavour = {final_item_flavours_list_2[0]} >")

                 # ---- size query creation ----

                # split size selector if multi select, only ever Regular or Large so easier to do
                if len(multi_size_selector_2) == 1:
                    final_size_select_2 = f"i.item_size='{multi_size_selector_2[0]}'"
                elif len(multi_size_selector_2) == 0:
                    final_size_select_2 = "i.item_size='Regular'"
                    itemInfoCol.error(f"Size defaults to Regular >")
                else:
                    final_size_select_2 = f"(i.item_size='{multi_size_selector_2[0]}' OR i.item_size = '{multi_size_selector_2[1]}')"

            if devmode:
                with st.expander("Initial Complex & Complicated Dynamic User Input Based SQL Query Creation"):
                    with st.echo():

                        # ---- flavour query creation ----

                        # ---- important ----
                        # required boolean flag for slightly altering the sql query (flavour is the only case with Null values so simple boolean flag is fine)
                        # if flavour is Null/None then we need to tweek the initial SELECT to get the correct (unique) item name
                        flavour_1_is_null = False

                        # split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                        # only required for flavour, as size can only be regular or large
                        # if only 1 flavour then 2 cases to deal with
                        if len(multi_flav_selector_1) == 1:
                            # check if this item has flavours by checking what was returned by the database for this item
                            if multi_flav_selector_1[0] is None:
                                # if there is no flavour for this then set the query to validate on NULL values (no = operator, no '')
                                final_flav_select_1 = f"i.item_flavour is NULL"
                                # also set null flavour flag to True so that final sql can be altered to output valid string (i.item_name, i.item_size, i.item_flavour) 
                                flavour_1_is_null = True
                            else:
                                # else just 1 valid flavour was selected so create standard query
                                final_flav_select_1 = f"i.item_flavour='{multi_flav_selector_1[0]}'"

                        # else if more than 1 flavour was selected then we must dynamically join them together so the query include OR statements
                        elif len(multi_flav_selector_1) > 1:
                            final_flav_select_1 = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_1)))
                            final_flav_select_1 = "(i.item_flavour=" + final_flav_select_1 + ")"

                        # else if no flavour was selected (any valid flavour was removed from the multiselect box by the user) then 2 cases to deal with      
                        elif len(multi_flav_selector_1) == 0:
                            final_flav_select_1 = f"i.item_flavour='{final_item_flavours_list[0]}'"
                            # first check the available flavours that were returned by the database for this item, if true user has removed the 'None' flavour option from multiselect
                            if multi_flav_selector_1[0] is None:
                                # if there is no flavour then set to validate on NULL
                                final_flav_select_1 = f"i.item_flavour is NULL"
                            else:      
                                # else (if the first flavour select option isn't None) then it means the user removed all from valid flavours from multiselect                
                                final_flav_select_1 = f"i.item_flavour='{final_item_flavours_list[0]}'"
                                # so add the 'default', aka first item in the flavours list, to the query and inform the user of what has happened
                                itemInfoCol.error(f"< Flavour = {final_item_flavours_list[0]}")

                        # ---- size query creation ----

                        # split size selector if multi select, only ever Regular or Large so easier to do
                        if len(multi_size_selector_1) == 1:
                            final_size_select_1 = f"i.item_size='{multi_size_selector_1[0]}'"
                        elif len(multi_size_selector_1) == 0:
                            final_size_select_1 = "i.item_size='Regular'"
                            itemInfoCol.error(f"< Size defaults to Regular")
                        else:
                            final_size_select_1 = f"(i.item_size='{multi_size_selector_1[0]}' OR i.item_size = '{multi_size_selector_1[1]}')"

        else:

            # if NOT advanced mode, but IS dev mode
            # aka needs echo/code print, but NO complex (flavour + size) query 
            if devmode:
                with st.expander("Complex Dynamic User Input Based Query Creation"):
                    # note the below queries are on one line for dev mode view due to code block printing excess spaces for \ new line formatting
                    st.markdown("###### The Live Executed Code")
                    with st.echo():
                        # complex (multi-step) but not complicated (significantly dynamic logic) queries as they require no flavour or size info,
                        # dealt with separately for scalability and readability (as opposed to one query with multiple boolean flags -> not scalable)

                        # ---- The Query Breakdown ----
                        # select count of names of each item sold, grouped by each unique item and for each hour of the day (e.g. 20 large mocha @ 9am, 15 large mocha @ 10am...)
                        # inner joins between customerdata -> essentially raw data that has been cleaned/valdiated
                        # and customeritems -> customer transactional data that has been normalised to first normal form (all unique records, all single values)
                        # joined on the transaction id (which is what allows the transactional 'customeritems' table to adhere to 1nf)
                        # where store, date, and item name are the users selected values

                        # left (item 1) query
                        cups_by_hour_query_2 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour, i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' GROUP BY d.timestamp, i.item_name"
                        hour_cups_data_2 = run_query(cups_by_hour_query_2)  

                        # right (item 2) query
                        cups_by_hour_query_3 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour, i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' GROUP BY d.timestamp, i.item_name"
                        hour_cups_data_3 = run_query(cups_by_hour_query_3)

                        # scroll right to check out your selections dynamically updating the queries in the live code blocks below :D
                        st.write("##")
                        st.markdown("###### The Resulting Dynamic Queries - Code Blocks")
                        st.markdown("Left Query (select 1) - **Scroll >**")
                        st.code(cups_by_hour_query_2, language="sql")
                        st.markdown("Right Query (select 2) - **Scroll >**")
                        st.code(cups_by_hour_query_3, language="sql")

            # else if NOT dev mode (and also NOT advanced mode)
            # aka NO echo, NO complex (flavour + size) query - so no excess comments or web app (single line) formatting needed
            else:     
                # left query (select 1)
                cups_by_hour_query_2 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id)\
                                WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' GROUP BY d.timestamp, i.item_name"
                hour_cups_data_2 = run_query(cups_by_hour_query_2)  

                # right query (select 2)
                cups_by_hour_query_3 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                    i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id)\
                                    WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' GROUP BY d.timestamp, i.item_name"
                hour_cups_data_3 = run_query(cups_by_hour_query_3)
   
               
        # TODO
        # LOOOOOOL - would love to but no not rn
        # try between 2 dates for advanced mode



        if advanced_options_1:
            # needed for assignment error (will be written again but meh)
            # right (item 2)
            if flavour_2_is_null == False:
                flavour_2_concat = ", i.item_flavour"
            else:
                flavour_2_concat = ""
            # left (item 1)
            if flavour_1_is_null == False:
                flavour_1_concat = ", i.item_flavour"
            else:
                flavour_1_concat = ""

            # purely for display in portfolio/dev mode
            CUPS_BY_HOURS_QUERY_2_ADV_DISPLAY = f"""SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                        CONCAT(i.item_name, i.item_size {flavour_1_concat}) AS item FROM redshift_customeritems i\
                                        INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                                        AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' AND {final_size_select_1}\
                                        AND {final_flav_select_1} GROUP BY d.timestamp, item"""
            # purely for display in portfolio/dev mode
            CUPS_BY_HOURS_QUERY_3_ADV_DISPLAY = f"""SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                        CONCAT(i.item_name, i.item_size {flavour_2_concat}) AS item FROM redshift_customeritems i\
                        INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                        AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' AND {final_size_select_2}\
                        AND {final_flav_select_2} GROUP BY d.timestamp, item"""

        # FIXME 
        # TODO - BETTER DISPLAY (as in add ur own explanation text for each 3 types of the display below)
        # PORTFOLIO 
        if advanced_options_1:
            # rip pep8 -> note long lines due to display for dev mode
            if devmode:
                with st.expander("The Final, Live Code Dynamic SQL Queries - Left Query (Item 1)"): # RENAME
                    st.markdown("##### :nerd_face: Extensively Commented Breakdown of Dynamic Query Creation (Live Code) :nerd_face:")
                    with st.echo():

                         # complex (multi-step) and complicated (significantly dynamic logic) queries
                        # as they require flavour and size info, and be null compatible 
                        # dealt with separately for scalability and readability (as opposed to one query with multiple boolean flags -> not scalable)

                        # ---- The Query Breakdown ----
                        # select count of names of each unique item sold, with the unique items = concatinated name + size + flavour (if not null)
                        # if flavour is null remove it from the concat in the select query
                        # then group each item by unique flavour + name + size 
                        # and for each hour of the day (e.g. 20 large mocha @ 9am, 15 large mocha @ 10am...)
                        # inner joins between customerdata -> essentially raw data that has been cleaned/valdiated
                        # and customeritems -> customer transactional data that has been normalised to first normal form (all unique records, all single values)
                        # joined on the transaction id (which is the field that allows the transactional 'customeritems' table to adhere to 1nf)
                        # where store, date, and item name are the users selected values

                        if flavour_1_is_null == False:
                            # if flag is False, a valid flavour is included in the flavour part of the query (AND i.flavour = "x" OR i.flavour = "y")
                            # so use it in the SELECT statement for finding unqiue items (unique item = item_name + unique size + unique flavour)
                            flavour_1_concat = ", i.item_flavour"
                        else:
                            # if flag is True, the query has been adjusted for Null values in the flavour part of the query (AND i.flavour is NULL)
                            # so remove it from the SELECT statement otherwise included NULL will invalidate it entirely (every i.itemname + i.itemsize will = NULL)
                            flavour_1_concat = ""  

                        # run the query
                        # scroll right or check out the below "Raw Text" dropdown to see this query before dynamic user inputs are added
                        cups_by_hour_query_2_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour, CONCAT(i.item_name, i.item_size {flavour_1_concat}) AS item FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' AND {final_size_select_1} AND {final_flav_select_1} GROUP BY d.timestamp, item"
                        hour_cups_data_2_adv = run_query(cups_by_hour_query_2_adv) 

                        # light formatting for the display you're looking at right now
                        st.write("")
                        st.markdown("##### :heart_eyes: The Resulting Dynamic Query :heart_eyes:")
                        st.write("Scroll The Code Below To See It In Action >")                        
                        st.code(cups_by_hour_query_2_adv, language="sql")   

                with st.expander("Resulting Dynamic Left Query - As Raw Text"):
                    st.markdown("###### Raw Text Version of Resulting Dynamic Query - No Scroll")
                    st.write("Change the above options (for the left/1st item) and watch this live update based on your inputs") 
                    st.write(CUPS_BY_HOURS_QUERY_2_ADV_DISPLAY) 

                with st.expander("The Final, Live Code Dynamic SQL Queries - Right Query (Item 2)"): # RENAME
                    st.markdown("##### :nerd_face: Extensively Commented Breakdown of Dynamic Query Creation (Live Code) :nerd_face:")
                    with st.echo():

                        # complex (multi-step) and complicated (significantly dynamic logic) queries
                        # as they require flavour and size info, and be null compatible 
                        # dealt with separately for scalability and readability (as opposed to one query with multiple boolean flags -> not scalable)

                        # ---- The Query Breakdown ----
                        # select count of names of each unique item sold, with the unique items = concatinated name + size + flavour (if not null)
                        # if flavour is null remove it from the concat in the select query
                        # then group each item by unique flavour + name + size 
                        # and for each hour of the day (e.g. 20 large mocha @ 9am, 15 large mocha @ 10am...)
                        # inner joins between customerdata -> essentially raw data that has been cleaned/valdiated
                        # and customeritems -> customer transactional data that has been normalised to first normal form (all unique records, all single values)
                        # joined on the transaction id (which is the field that allows the transactional 'customeritems' table to adhere to 1nf)
                        # where store, date, and item name are the users selected values

                        if flavour_2_is_null == False:
                            # if flag is False, a valid flavour is included in the flavour part of the query (AND i.flavour = "x" OR i.flavour = "y")
                            # so use it in the SELECT statement for finding unqiue items (unique item = item_name + unique size + unique flavour)
                            flavour_2_concat = ", i.item_flavour"
                        else:
                            # if flag is True, the query has been adjusted for Null values in the flavour part of the query (AND i.flavour is NULL)
                            # so remove it from the SELECT statement otherwise included NULL will invalidate it entirely (every i.itemname + i.itemsize will = NULL)
                            flavour_2_concat = ""                        

                        # run the query
                        # scroll right or check out the below "Raw Text" dropdown to see this query before dynamic user inputs are added
                        cups_by_hour_query_3_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour, CONCAT(i.item_name, i.item_size {flavour_2_concat}) AS item FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' AND {final_size_select_2} AND {final_flav_select_2} GROUP BY d.timestamp, item"
                        hour_cups_data_3_adv = run_query(cups_by_hour_query_3_adv)

                        # light formatting for the display you're looking at right now
                        st.write("")
                        st.markdown("##### :heart_eyes: The Resulting Dynamic Query :heart_eyes:")
                        st.write("Scroll The Code Below To See It In Action >")
                        st.code(cups_by_hour_query_3_adv, language="sql")    

                with st.expander("Resulting Dynamic Right Query - As Raw Text"):
                    st.markdown("###### Raw Text Version of Resulting Dynamic Query - No Scroll")
                    st.write("Change the above options (for the right/2nd item) and watch this live update based on your inputs") 
                    st.write(CUPS_BY_HOURS_QUERY_3_ADV_DISPLAY) 

            # if no dev mode, but complex (flavour + size) query            
            else:
                # no need for excess comments as no echo

                if flavour_1_is_null == False:
                    flavour_1_concat = ", i.item_flavour"
                else:
                    flavour_1_concat = ""

                cups_by_hour_query_2_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                            CONCAT(i.item_name, i.item_size {flavour_1_concat}) AS item FROM redshift_customeritems i\
                                            INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                                            AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' AND {final_size_select_1}\
                                            AND {final_flav_select_1} GROUP BY d.timestamp, item"
                hour_cups_data_2_adv = run_query(cups_by_hour_query_2_adv)                                   

                if flavour_2_is_null == False:
                    flavour_2_concat = ", i.item_flavour"
                else:
                    flavour_2_concat = ""
                
                cups_by_hour_query_3_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                    CONCAT(i.item_name, i.item_size {flavour_2_concat}) AS item FROM redshift_customeritems i\
                                    INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                                    AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' AND {final_size_select_2}\
                                    AND {final_flav_select_2} GROUP BY d.timestamp, item"
                hour_cups_data_3_adv = run_query(cups_by_hour_query_3_adv)   

        st.write("##")

        # ---- finally create and print the altair chart of the results... phew ----

        # left query (item 1)

        # empty lists used for transforming db data for df
        just_names_list_2 = []
        just_hour_list_2 = []
        just_cupcount_list_2 = []

        # if advanced mode use the advanced (_adv) query, else use the simple one
        if advanced_options_1:
            for cups_data in hour_cups_data_2_adv:
                just_cupcount_list_2.append(cups_data[0])
                just_hour_list_2.append(cups_data[1])
                just_names_list_2.append(cups_data[2])
        else:
            for cups_data in hour_cups_data_2:
                just_cupcount_list_2.append(cups_data[0])
                just_hour_list_2.append(cups_data[1])
                just_names_list_2.append(cups_data[2])
        

        
        # FIXME - ASAP!
        # PORTFOLIO - ADD THIS AND ECHO SOMEWHERE PLSSS!! 
        # THEN QUICKLY SEE IF CAN FIX THE STRING THING BUT COULD LEAVE FOR NOW TBF
        # THEN LEGIT DONE ON THIS ONE FOR NOW BOSH


        # right query (item 2)

        # empty lists used for transforming db data for df
        just_names_list_3 = []
        just_hour_list_3 = []
        just_cupcount_list_3 = []

        # if advanced mode use the advanced (_adv) query, else use the simple one
        if advanced_options_1:
            for cups_data in hour_cups_data_3_adv:
                just_cupcount_list_3.append(cups_data[0])
                just_hour_list_3.append(cups_data[1])
                just_names_list_3.append(cups_data[2])
        else:
            for cups_data in hour_cups_data_3:
                just_cupcount_list_3.append(cups_data[0])
                just_hour_list_3.append(cups_data[1])
                just_names_list_3.append(cups_data[2])

        # extended one of the lists with the other for the final dataframe 
        just_names_list_2.extend(just_names_list_3)
        just_hour_list_2.extend(just_hour_list_3)
        just_cupcount_list_2.extend(just_cupcount_list_3)

        # create the dataframe
        source2 = pd.DataFrame({
        "DrinkName": just_names_list_2,
        "CupsSold":  just_cupcount_list_2,
        "HourOfDay": just_hour_list_2
        })



        # setup barchart
        bar_chart2 = alt.Chart(source2).mark_bar().encode(
            color="DrinkName:N",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300)

        # setup text labels for barchart
        text2 = alt.Chart(source2).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        # render the chart
        st.altair_chart(bar_chart2 + text2, use_container_width=True)



        # PIE CHART - OBVS MOVE BUT DO KEEP THIS CODE AS LIKELY DO A PIE CHART SOON ENOUGH
        #pie_chart1 = alt.Chart(source2).mark_arc(innerRadius=50).encode(
        #    #color="DrinkName:N", # x="month(Date):O",
        #    theta="sum(CupsSold):Q",
        #    color="HourOfDay:N"
        #).properties(height=300)
        #
        #st.altair_chart(pie_chart1, use_container_width=True)

        st.write("##")
        st.write("##")
        st.write("---")


    # ---- end compare 2 items altair chart section ----






    ################### NEW #######################


    # CHART name container
    with st.container():

        # note - i created this in week 1, hence why the duplication
        # obvs as above compare example can be done by extending lists into 1 field
        # but logic still good so straight ported over and tweaked

        # need to update this so time of day is a string (actual word)
        # since these are tuples won't be straightforward

        breakfast_sales = db.get_cups_sold_by_time_of_day(1)
        earlylunch_sales = db.get_cups_sold_by_time_of_day(2)
        latelunch_sales = db.get_cups_sold_by_time_of_day(3)
        afternoon_sales = db.get_cups_sold_by_time_of_day(4)
        
        ChaiLatte_Breaky = breakfast_sales[0]
        Cortado_Breaky = breakfast_sales[1]
        Espresso_Breaky = breakfast_sales[2]
        FlatWhite_Breaky = breakfast_sales[3]
        FlavouredHotChocolate_Breaky = breakfast_sales[4]
        FlavouredIcedLatte_Breaky = breakfast_sales[5] #####
        FlavouredLatte_Breaky = breakfast_sales[6]
        Frappes_Breaky = breakfast_sales[7]
        GlassOfMilk_Breaky = breakfast_sales[8]
        HotChocolate_Breaky = breakfast_sales[9]
        IcedLatte_Breaky = breakfast_sales[10]
        Latte_Breaky = breakfast_sales[11]
        LuxuryHotChocolate_Breaky = breakfast_sales[12]
        Mocha_Breaky = breakfast_sales[13]
        RedLabelTea_Breaky = breakfast_sales[14]
        Smoothies_Breaky = breakfast_sales[15] 
        SpecialityTea_Breaky = breakfast_sales[16] #####

        ChaiLatte_Lunch = earlylunch_sales[0]
        Cortado_Lunch = earlylunch_sales[1]
        Espresso_Lunch = earlylunch_sales[2]
        FlatWhite_Lunch = earlylunch_sales[3]
        FlavouredHotChocolate_Lunch = earlylunch_sales[4]
        FlavouredIcedLatte_Lunch = earlylunch_sales[5]
        FlavouredLatte_Lunch = earlylunch_sales[6]
        Frappes_Lunch = earlylunch_sales[7]
        GlassOfMilk_Lunch = earlylunch_sales[8]
        HotChocolate_Lunch = earlylunch_sales[9]
        IcedLatte_Lunch = earlylunch_sales[10]
        Latte_Lunch = earlylunch_sales[11]
        LuxuryHotChocolate_Lunch = earlylunch_sales[12]
        Mocha_Lunch = earlylunch_sales[13]
        RedLabelTea_Lunch = earlylunch_sales[14]
        Smoothies_Lunch = earlylunch_sales[15]
        SpecialityTea_Lunch = earlylunch_sales[16] #####

        ChaiLatte_LateLunch = latelunch_sales[0]
        Cortado_LateLunch = latelunch_sales[1]
        Espresso_LateLunch = latelunch_sales[2]
        FlatWhite_LateLunch = latelunch_sales[3]
        FlavouredHotChocolate_LateLunch = latelunch_sales[4]
        FlavouredIcedLatte_LateLunch = latelunch_sales[5] #####
        FlavouredLatte_LateLunch = latelunch_sales[6]
        Frappes_LateLunch = latelunch_sales[7]
        GlassOfMilk_LateLunch = latelunch_sales[8]
        HotChocolate_LateLunch = latelunch_sales[9]
        IcedLatte_LateLunch = latelunch_sales[10]
        Latte_LateLunch = latelunch_sales[11]
        LuxuryHotChocolate_LateLunch = latelunch_sales[12]
        Mocha_LateLunch = latelunch_sales[13]
        RedLabelTea_LateLunch = latelunch_sales[14]
        Smoothies_LateLunch = latelunch_sales[15]
        SpecialityTea_LateLunch = latelunch_sales[16] #####

        ChaiLatte_Afternoon = afternoon_sales[0]
        Cortado_Afternoon = afternoon_sales[1]
        Espresso_Afternoon = afternoon_sales[2]
        FlatWhite_Afternoon = afternoon_sales[3]
        FlavouredHotChocolate_Afternoon = afternoon_sales[4]
        FlavouredIcedLatte_Afternoon = afternoon_sales[5] #####
        FlavouredLatte_Afternoon = afternoon_sales[6]
        Frappes_Afternoon = afternoon_sales[7]
        GlassOfMilk_Afternoon = afternoon_sales[8]
        HotChocolate_Afternoon = afternoon_sales[9]
        IcedLatte_Afternoon = afternoon_sales[10]
        Latte_Afternoon = afternoon_sales[11]
        LuxuryHotChocolate_Afternoon = afternoon_sales[12]
        Mocha_Afternoon = afternoon_sales[13]
        RedLabelTea_Afternoon = afternoon_sales[14]
        Smoothies_Afternoon = afternoon_sales[15]
        SpecialityTea_Afternoon = afternoon_sales[16] #####

        # like what dates is this, proper info on why no flavours, general info, etc etc

        # least popular as no flavours duh (make this clear)
        st.write("### Item Popularity (Volume Sold)") # time of day popularity or sumnt?
        st.write("##### All Days - All Stores - Not Core Items")
        st.write("Includes all items except the top 3 products for greater readability and analysis")
        st.write("Consider removing the least popular/lowest volume products for newer ones/trending products, particularly if profit margins are small")
        st.write("##")

        
        
        source6 = pd.DataFrame({
        "CoffeeType": [FlatWhite_Breaky[1], FlatWhite_Lunch[1],FlatWhite_LateLunch[1],FlatWhite_Afternoon[1],
                        Latte_Breaky[1], Latte_Lunch[1],Latte_LateLunch[1],Latte_Afternoon[1],
                        FlavouredLatte_Breaky[1], FlavouredLatte_Lunch[1],FlavouredLatte_LateLunch[1],FlavouredLatte_Afternoon[1],
                        ChaiLatte_Breaky[1], ChaiLatte_Lunch[1], ChaiLatte_LateLunch[1],ChaiLatte_Afternoon[1],
                        FlavouredHotChocolate_Breaky[1], FlavouredHotChocolate_Lunch[1], FlavouredHotChocolate_LateLunch[1], FlavouredHotChocolate_Afternoon[1],
                        HotChocolate_Breaky[1], HotChocolate_Lunch[1], HotChocolate_LateLunch[1],HotChocolate_Afternoon[1],
                        LuxuryHotChocolate_Breaky[1], LuxuryHotChocolate_Lunch[1], LuxuryHotChocolate_LateLunch[1], LuxuryHotChocolate_Afternoon[1],
                        IcedLatte_Breaky[1], IcedLatte_Lunch[1], IcedLatte_LateLunch[1],IcedLatte_Afternoon[1],
                        Espresso_Breaky[1], Espresso_Lunch[1], Espresso_LateLunch[1],Espresso_Afternoon[1],
                        Frappes_Breaky[1], Frappes_Lunch[1], Frappes_LateLunch[1],Frappes_Afternoon[1],
                        Mocha_Breaky[1], Mocha_Lunch[1], Mocha_LateLunch[1],Mocha_Afternoon[1],
                        Smoothies_Breaky[1], Smoothies_Lunch[1], Smoothies_LateLunch[1], Smoothies_Afternoon[1],
                        GlassOfMilk_Breaky[1], GlassOfMilk_Lunch[1], GlassOfMilk_LateLunch[1], GlassOfMilk_Afternoon[1],
                        Cortado_Breaky[1], Cortado_Lunch[1], Cortado_LateLunch[1], Cortado_Afternoon[1],
                        RedLabelTea_Breaky[1], RedLabelTea_Lunch[1], RedLabelTea_LateLunch[1], RedLabelTea_Afternoon[1]], 

        "CupsSold":  [FlatWhite_Breaky[0],FlatWhite_Lunch[0],FlatWhite_LateLunch[0],FlatWhite_Afternoon[0],
                        Latte_Breaky[0],Latte_Lunch[0],Latte_LateLunch[0],Latte_Afternoon[0],
                        FlavouredLatte_Breaky[0],FlavouredLatte_Lunch[0],FlavouredLatte_LateLunch[0],FlavouredLatte_Afternoon[0],
                        ChaiLatte_Breaky[0],ChaiLatte_Lunch[0], ChaiLatte_LateLunch[0], ChaiLatte_Afternoon[0],
                        FlavouredHotChocolate_Breaky[0],FlavouredHotChocolate_Lunch[0], FlavouredHotChocolate_LateLunch[0], FlavouredHotChocolate_Afternoon[0],
                        HotChocolate_Breaky[0], HotChocolate_Lunch[0], HotChocolate_LateLunch[0],HotChocolate_Afternoon[0],
                        LuxuryHotChocolate_Breaky[0],LuxuryHotChocolate_Lunch[0], LuxuryHotChocolate_LateLunch[0], LuxuryHotChocolate_Afternoon[0],
                        IcedLatte_Breaky[0],IcedLatte_Lunch[0], IcedLatte_LateLunch[0],IcedLatte_Afternoon[0],
                        Espresso_Breaky[0],Espresso_Lunch[0], Espresso_LateLunch[0],Espresso_Afternoon[0],
                        Frappes_Breaky[0],Frappes_Lunch[0], Frappes_LateLunch[0],Frappes_Afternoon[0],
                        Mocha_Breaky[0],Mocha_Lunch[0], Mocha_LateLunch[0],Mocha_Afternoon[0],
                        Smoothies_Breaky[0],Smoothies_Lunch[0], Smoothies_LateLunch[0], Smoothies_Afternoon[0],
                        GlassOfMilk_Breaky[0],GlassOfMilk_Lunch[0], GlassOfMilk_LateLunch[0], GlassOfMilk_Afternoon[0],
                        Cortado_Breaky[0],Cortado_Lunch[0], Cortado_LateLunch[0], Cortado_Afternoon[0],
                        RedLabelTea_Breaky[0],RedLabelTea_Lunch[0], RedLabelTea_LateLunch[0], RedLabelTea_Afternoon[0]], 

        "TimeOfDay": [FlatWhite_Breaky[2],FlatWhite_Lunch[2],FlatWhite_LateLunch[2],FlatWhite_Afternoon[2],
                        Latte_Breaky[2],Latte_Lunch[2],Latte_LateLunch[2],Latte_Afternoon[2],
                        FlavouredLatte_Breaky[2],FlavouredLatte_Lunch[2],FlavouredLatte_LateLunch[2],FlavouredLatte_Afternoon[2],
                        ChaiLatte_Breaky[2],ChaiLatte_Lunch[2], ChaiLatte_LateLunch[2],ChaiLatte_Afternoon[2],
                        FlavouredHotChocolate_Breaky[2],FlavouredHotChocolate_Lunch[2], FlavouredHotChocolate_LateLunch[2],FlavouredHotChocolate_Afternoon[2],
                        HotChocolate_Breaky[2],HotChocolate_Lunch[2], HotChocolate_LateLunch[2],HotChocolate_Afternoon[2],
                        LuxuryHotChocolate_Breaky[2],LuxuryHotChocolate_Lunch[2], LuxuryHotChocolate_LateLunch[2], LuxuryHotChocolate_Afternoon[2],
                        IcedLatte_Breaky[2],IcedLatte_Lunch[2], IcedLatte_LateLunch[2],IcedLatte_Afternoon[2],
                        Espresso_Breaky[2],Espresso_Lunch[2], Espresso_LateLunch[2],Espresso_Afternoon[2],
                        Frappes_Breaky[2],Frappes_Lunch[2], Frappes_LateLunch[2],Frappes_Afternoon[2],
                        Mocha_Breaky[2],Mocha_Lunch[2], Mocha_LateLunch[2],Mocha_Afternoon[2],
                        Smoothies_Breaky[2],Smoothies_Lunch[2], Smoothies_LateLunch[2], Smoothies_Afternoon[2],
                        GlassOfMilk_Breaky[2],GlassOfMilk_Lunch[2], GlassOfMilk_LateLunch[2],GlassOfMilk_Afternoon[2],
                        Cortado_Breaky[2],Cortado_Lunch[2], Cortado_LateLunch[2],Cortado_Afternoon[2],
                        RedLabelTea_Breaky[2],RedLabelTea_Lunch[2],RedLabelTea_LateLunch[2], RedLabelTea_Afternoon[2]]
                    })

        bar_chart6 = alt.Chart(source6).mark_bar().encode(
            color="TimeOfDay:N",
            x="CupsSold:Q",
            y="CoffeeType:N"
        ).properties(height=600)

        text6 = alt.Chart(source6).mark_text(dx=-10, dy=3, color='white', fontSize=10, fontWeight=600).encode(
            x=alt.X('CupsSold:Q', stack='zero'),
            y=alt.Y('CoffeeType:N'),
            detail='TimeOfDay:N',
            text=alt.Text('CupsSold:Q', format='.0f')
        )

        st.altair_chart(bar_chart6 + text6, use_container_width=True)

        afternoon_best_sales = max(afternoon_sales)
        afternoon_worst_sales = min(afternoon_sales)
        latelunch_sales_best_sales = max(afternoon_sales)
        latelunch_sales_worst_sales = min(afternoon_sales)
        earlylunch_sales_best_sales = max(afternoon_sales)
        earlylunch_sales_worst_sales = min(afternoon_sales)
        breakfast_sales_best_sales = max(afternoon_sales)
        breakfast_sales_worst_sales = min(afternoon_sales)                        
        all_times_combined_sales = afternoon_sales + latelunch_sales + earlylunch_sales + breakfast_sales
        all_times_combined_best_sales = max(all_times_combined_sales)
        all_times_combined_worst_sales = min(all_times_combined_sales)

        ToDcol1, ToDcol2, ToDcol3 = st.columns(3)

        # N0TE THE DELTA SHOULD BE AN AVERAGE DUH!
        # as in combining all times together (so the top top or the worst worst, not like an average - tho do want an avg?)
        combined_best_name, combined_best_count = all_times_combined_best_sales[1], all_times_combined_best_sales[0]
        combined_worst_name, combined_worst_count = all_times_combined_worst_sales[1], all_times_combined_worst_sales[0]
        break_best_name, break_best_count = breakfast_sales_best_sales[1], breakfast_sales_best_sales[0]
        break_worst_name, break_worst_count = breakfast_sales_worst_sales[1], breakfast_sales_worst_sales[0]

        with ToDcol1:
            ToDselect = st.radio(label="Time Of Day", options=["Breakfast","Late Lunch","Early Lunch","Afternoon","All Combined"])
        
        if ToDselect == "Breakfast":
            ToDcol2.write("Best Sales")
            ToDcol2.metric(label=break_best_name, value=break_best_count, delta=1, delta_color="normal")
            ToDcol3.write("Worst Sales")
            ToDcol3.metric(label=break_worst_name, value=break_worst_count, delta=1, delta_color="normal")

run()


