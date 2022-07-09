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

        average_hourcups = sum(results_dict.values()) / len(results_dict.values())

        # create a new dictionary from hour/cups dictionary but sorted
        sort_by_value = dict(sorted(results_dict.items(), key=lambda x: x[1]))   
        # create a list of formatted strings with times and cups sold including am or pm based on the time
        sort_by_value_formatted_list = list(map(lambda x: (f"{x[0]}pm [{x[1]} cups sold]") if x[0] > 11 else (f"{x[0]}am [{x[1]} cups sold]"), sort_by_value.items()))

        # list the keys (times, ordered) only, slice the first and last elements in the array (list) [start:stop:step]
        worst_time, best_time = list(sort_by_value.keys())[::len(sort_by_value.keys())-1]
        worst_performer, best_performer = sort_by_value_formatted_list[::len(sort_by_value_formatted_list)-1]

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
            ###### TO DO ASAP...\n
            Average Sales Per Hour: {average_hourcups:.2f} cups sold\n
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
            altairChartCol1, altairChartCol2 = st.columns([2,2])
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



    # ---- NEW ----

        
    # ALTAIR CHART product sold by hour of day (COMPARE 2?!) - INDIVIDUAL ITEM VERSION OF ABOVE
    with st.container():
        st.write(f"### :bulb: Insight - Compare Two Items") 

        # new store selector
        store_selector_2 = st.selectbox(label="Choose The Store", key="store_select_2", options=stores_list, index=0) 
        
        # new date selector
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
                st.info("Advanced Mode : ON")
            else:
                st.warning("Try Advanced Mode!")

         # ---- new [testing] - advanced mode ----

        if advanced_options_1:
            # left col (item 1)
            with item1Col:
                item_flavours_1 = run_query(f"SELECT DISTINCT i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}' AND i.item_name = '{item_selector_1}';")
                final_item_flavours_list = []
                dont_print_2 = [final_item_flavours_list.append(flavour[0]) for flavour in item_flavours_1]
                # flav_selector_1 = st.selectbox(label=f"Choose A Flavour For {item_selector_1}", key="flav_selector_1", options=final_item_flavours_list, index=0)  
                multi_flav_selector_1 = st.multiselect(label=f"Choose A Flavour For {item_selector_1}", key="multi_flav_select_1", options=final_item_flavours_list, default=final_item_flavours_list[0])
                # size_selector_1 = st.selectbox(label=f"Choose A Size For {item_selector_1}", key="size_selector_1", options=["Regular","Large"], index=0)
                multi_size_selector_1 = st.multiselect(label=f"Choose A Size For {item_selector_1}", key="multi_size_select_1", options=["Regular","Large"], default="Regular")
            

                # PORTFOLIO 
                # split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                if len(multi_flav_selector_1) == 1:
                    final_flav_select_1 = f"i.item_flavour='{multi_flav_selector_1[0]}'"
                elif len(multi_flav_selector_1) > 1:
                    final_flav_select_1 = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_1)))
                    final_flav_select_1 = "(i.item_flavour=" + final_flav_select_1 + ")"
                elif len(multi_flav_selector_1) == 0:
                    final_flav_select_1 = f"i.item_flavour='{final_item_flavours_list[0]}'"
                    itemInfoCol.error(f"Flavour = {final_item_flavours_list[0]} >")

                # split size selector if multi select, only ever Regular or Large so easier to do
                if len(multi_size_selector_1) == 1:
                    final_size_select_1 = f"i.item_size='{multi_size_selector_1[0]}'"
                elif len(multi_size_selector_1) == 0:
                    final_size_select_1 = "i.item_size='Regular'"
                    itemInfoCol.error(f"Size defaults to Regular >")
                else:
                    final_size_select_1 = f"(i.item_size='{multi_size_selector_1[0]}' OR i.item_size = '{multi_size_selector_1[1]}')"


            # right col (item 2)
            with item2Col:
                item_flavours_2 = run_query(f"SELECT DISTINCT i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}' AND i.item_name = '{item_selector_2}';")
                final_item_flavours_list_2 = []
                dont_print_3 = [final_item_flavours_list_2.append(flavour[0]) for flavour in item_flavours_2]
                # flav_selector_2 = st.selectbox(label=f"Choose A Flavour For {item_selector_2}", key="flav_selector_2", options=final_item_flavours_list, index=0)  
                multi_flav_selector_2 = st.multiselect(label=f"Choose A Flavour For {item_selector_2}", key="multi_flav_select_2", options=final_item_flavours_list_2, default=final_item_flavours_list_2[0])
                # size_selector_2 = st.selectbox(label=f"Choose A Size For {item_selector_2}", key="size_selector_2", options=["Regular","Large"], index=0)
                multi_size_selector_2 = st.multiselect(label=f"Choose A Size For {item_selector_2}", key="multi_size_select_2", options=["Regular","Large"], default="Regular")


                # PORTFOLIO 
                # split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                if len(multi_flav_selector_2) == 1:
                    final_flav_select_2 = f"i.item_flavour='{multi_flav_selector_2[0]}'"
                elif len(multi_flav_selector_2) > 1:
                    final_flav_select_2 = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_2)))
                    final_flav_select_2 = "(i.item_flavour=" + final_flav_select_2 + ")"
                elif len(multi_flav_selector_2) == 0:
                    final_flav_select_2 = f"i.item_flavour='{final_item_flavours_list_2[0]}'"
                    itemInfoCol.error(f"< Flavour = {final_item_flavours_list_2[0]}")

                # split size selector if multi select, only ever Regular or Large so easier to do
                if len(multi_size_selector_2) == 1:
                    final_size_select_2 = f"i.item_size='{multi_size_selector_2[0]}'"
                elif len(multi_size_selector_2) == 0:
                    final_size_select_2 = "i.item_size='Regular'"
                    itemInfoCol.error(f"< Size defaults to Regular")
                else:
                    final_size_select_2 = f"(i.item_size='{multi_size_selector_2[0]}' OR i.item_size = '{multi_size_selector_2[1]}')"

               
               
        # get flavour and size for the given main item
        # display side by side in columns
        # make the query extension and send the query
        # display the shit back
        # try between 2 dates for advanced mode
        # (legit could go up to 4 yanno?!) - but not rn
        # add echo
        # move on

       
        st.write("##")


        # CRITICAL
        # OBVS SPLITTING THE QUERY FOR MULTI SELECT
        # & 
        # IF NONE (may have to rip the whole part of the query but lets see)



        # MAKE FUNCTION AND REUSE THE QUERY FFS

        # left query (select 1)
        cups_by_hour_query_2 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                            i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id)\
                            WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' GROUP BY d.timestamp, i.item_name"
        hour_cups_data_2 = run_query(cups_by_hour_query_2)

        cups_by_hour_query_2_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                    CONCAT(i.item_name, i.item_size, i.item_flavour) AS item FROM redshift_customeritems i\
                                    INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                                    AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' AND {final_size_select_1}\
                                    AND {final_flav_select_1} GROUP BY d.timestamp, item"
        hour_cups_data_2_adv = run_query(cups_by_hour_query_2_adv)                                   

        # right query (select 2)
        cups_by_hour_query_3 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                            i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id)\
                            WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' GROUP BY d.timestamp, i.item_name"
        hour_cups_data_3 = run_query(cups_by_hour_query_3)

        cups_by_hour_query_3_adv = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                            CONCAT(i.item_name, i.item_size, i.item_flavour) AS item FROM redshift_customeritems i\
                            INNER JOIN redshift_customerdata d ON (i.transaction_id = d.transaction_id) WHERE store = '{store_selector_2}'\
                            AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' AND {final_size_select_2}\
                            AND {final_flav_select_2} GROUP BY d.timestamp, item"
        hour_cups_data_3_adv = run_query(cups_by_hour_query_3_adv)   


        #print(hour_cups_data_2_adv) 
        #print(hour_cups_data_3_adv)

        st.write("##")

        # create and print an altair chart

        # MAKE WHOLE THING A FUNCTION (FUNCTION OF FUNCTIONS TBF - BREAK UP AT RELEVANT POINTS) AND CAN REUSE IT TOO! 

        just_names_list_2 = []
        just_hour_list_2 = []
        just_cupcount_list_2 = []

        # if advanced mode use the more in depth query, else use the simple one (could merge if statement/for loop section here with below btw)
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
        
        just_names_list_3 = []
        just_hour_list_3 = []
        just_cupcount_list_3 = []

        # if advanced mode use the more in depth query, else use the simple one
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

        just_names_list_2.extend(just_names_list_3)
        just_hour_list_2.extend(just_hour_list_3)
        just_cupcount_list_2.extend(just_cupcount_list_3)

        source2 = pd.DataFrame({
        "DrinkName": just_names_list_2,
        "CupsSold":  just_cupcount_list_2,
        "HourOfDay": just_hour_list_2
        })

        source3 = pd.DataFrame({
        "DrinkName": just_names_list_3,
        "CupsSold":  just_cupcount_list_3,
        "HourOfDay": just_hour_list_3
        })

        bar_chart2 = alt.Chart(source2).mark_bar().encode(
            color="DrinkName:N", # x="month(Date):O",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300)

        text2 = alt.Chart(source2).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

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





############# FOR MENU PRINT ################
    
    # new store selector
    store_selector_4 = st.selectbox(label="Choose The Store", key="store_select_4", options=stores_list, index=0) 
    
    # get every valid unique combination of item, size and flavour, returned as tuple for the selected store only
    get_menu = run_query(f"SELECT DISTINCT i.item_name, i.item_size, i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_4}'")
    # query for all below
    # get_menu = run_query("SELECT DISTINCT item_name, item_size, item_flavour AS unique_items FROM redshift_customeritems")
    final_menu = []
    for item in get_menu:
        final_item = []
        # remove any None types from the tuple returned from the query
        dont_print = [final_item.append(subitem) for subitem in item if subitem is not None]
        # join each element of iterable in to one string with spaces between
        menu_item = (" ".join(final_item))
        # format and append all items to a list for user selection
        menu_item = menu_item.title().strip()
        final_menu.append(menu_item)

    # select any item from the store for comparison
    item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_4}", key="item_selector_1", options=final_menu, index=0) 

    st.write("##")
    st.write("---")


###############################################











    
    ## ADD TO CONTAINER BELOW


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

    # CHART name container
    with st.container():

        # DO LIKE LEAST POP, MOST POP - OBVS FLAV ONES HAVE FLAVS SO THIS IS WHY THEY WANNA BE SECTIONED AGAIN THEMSELVES BUT MEH ANOTHER TIME
        st.write("#### Less Popular - All Days - All Stores - Volume Sold (Popularity)") # time of day popularity or sumnt?
        st.write("Consider removing the least popular products (lowest volume) for new ones, particularly if profit margins are small")
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
            color="TimeOfDay:N", # x="month(Date):O",
            x="CupsSold:Q",
            y="CoffeeType:N"
        ).properties(height=600, width=1000)

        text6 = alt.Chart(source6).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('CupsSold:Q', stack='zero'),
            y=alt.Y('CoffeeType:N'),
            detail='TimeOfDay:N',
            text=alt.Text('CupsSold:Q', format='.0f')
        )

        st.altair_chart(bar_chart6 + text6, use_container_width=True)




run()


