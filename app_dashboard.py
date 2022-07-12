# app_dashboard.py

# ---- notes ----

# 1. manually adheres to pep8 as best possible, no linter used as trying to learn pep8 styling as much as possible as a jnr dev (syling is important mkay)
# 1b. but kinda rip pep8 because parts are messy (e.g. excessively long lines) but is entirely due to portfolio/dev mode display needs 
# 2. as per 1b, there is some repeated code but entirely due to porfolio + the way echo works (method which runs & displays live code on the web app @ the same time)
# 2b. as per 2, would ideally have placed things in cached functions to stop excess calls but again, due to echo/portfolio mode this isn't really possible
# 3. due to weird cffi module issues must be built with python version 3.7 (not 3.9 where it was developed), important for pushing to streamlit cloud for web app
# 4. entirely done by me for my group project, streamlit was not included in any of our lessons I just think its a great too and works perf with snowflake
#       - others will be using grafana or metabase, though clean doesn't allow for dynamic user selections, multipage dashboard web app
#       - i feel this not only shows my drive to go above and beyond to wow the end user, but also my ability to independently learn new frameworks   
# 5. comments are excessive for portfolio mode, i am a big comment enjoyer but normally would not comment so extensively, particularly where code is self-referencing 


# ---- imports ----

# for web app 
import streamlit as st
import snowflake.connector
import streamlit.components.v1 as stc
from streamlit.errors import StreamlitAPIException
# for date time objects
import datetime # from datetime import datetime
# for db integration
import db_integration as db
# for images and img manipulation
import PIL
# for artist
import artist as arty


# ---- page setup ----

# set page config needs to be the first streamlit action that is run for it to work, sets the layout default to wide
def on_load():
    st.set_page_config(layout="wide")

# catch error in case that file is reloaded locally so app thinks config hasn't run first
try: 
    on_load()
except StreamlitAPIException:
    pass
 

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


# ---- functions ----

def split_metric_eafp(results:tuple, vals_or_delta:str) -> list: # big type hint enjoyer btw
    """
    creates list of query results for the metric values and delta, 
    saves doing a massive switch case since try excepts are needed to set either value or 0
    """
    delta_result = []
    values_result = []
    # loop the given list from the query and place it into a new list while performing try except to set either its value or 0 
    for value in results:
        try:
            # if has data in value[i] (which is metricVals/delta[0][i]), set it to list outside of loop to return on complete
            if vals_or_delta == "delta":
                if value == None:
                    delta_result.append(0)
                else:
                    delta_result.append(value)
            else:
                if value == None:
                    values_result.append(0)
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
        dev_mode = st.checkbox(label="Portfolio Mode ", key="devmode-dash")
        if dev_mode:
            WIDE_MODE_INFO = """
            Portfolio Mode Active\n
            Check out expanders to see the live code blocks which have executed
            """
            st.info(WIDE_MODE_INFO)

    # HEADER section
    topcol1, topcol2 = st.columns([1,5])
    topcol2.markdown("# Your Dashboard")
    try:
        topcol1.image("imgs/cafe_sign.png", width=120)
    except:
        st.write("")
    st.write("##")
    st.write("---")


    # ---- Daily Snapshot Section ----

    # DATE SELECTER container
    with st.container():

        st.markdown("### Daily Snapshot")
        #st.write("##")
        topMetricSelectCol1, topMetricSelectCol2 = st.columns(2)

        with topMetricSelectCol1:
            dateme = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate)  

        # PORTFOLIO 
        if dev_mode:
            with st.expander("Dynamic User Created SQL Queries (Dictionary Switch, Map, Join)"):
                with st.echo():
                    # note 1 - data hosted on redshift, moved to s3 bucket, then transferred to snowflake warehouse
                    # note 2 - query functions would be in a separate module, left here to show functionality through portfolio/dev mode
                    with topMetricSelectCol2:
                        selected_stores = st.multiselect(label='What Stores Would You Like Info On?', default=['All'],
                                    options=['Uppingham', 'Longridge', 'Chesterfield', 'London Camden', 'London Soho', 'All', 'Only London', 'Only Outside London'])

                        # dictionary switch case, access keys instead of 5x if statements
                        stores_query_selector = {"Only London":"AND store_name = 'London Camden' OR store_name = 'London Soho'", 
                                                'Only Outside London':"AND store_name = 'Uppingham' OR store_name = 'Longridge' OR store_name = 'Chesterfield'",
                                                'All':"AND store_name = 'Uppingham' OR store_name = 'Longridge' OR store_name = 'Chesterfield' OR store_name = 'London Camden' OR store_name = 'London Soho'",
                                                'Uppingham':"AND store_name = 'Uppingham'", 'Longridge':"AND store_name = 'Longridge'", 'Chesterfield':"AND store_name = 'Chesterfield'",
                                                'London Camden':"AND store_name = 'London Camden'", 'London Soho':"AND store_name = 'London Soho'"}

                        # does still need true switch case to create the final part of the store select query,
                        # needed for cases like "Only London" + "Chesterfield", in which case "Only" is the override,
                        # with all still having the highest precedent, and will be set to "All" if user selects nothing

                        # if only one thing selected, grab it from the dictionary switch case
                        if len(selected_stores) == 1:
                            final_stores = stores_query_selector[selected_stores[0]]
                        # if nothing selected use "All" from dictionary switch case
                        elif len(selected_stores) == 0:
                            final_stores = stores_query_selector["All"]
                        elif "All" in selected_stores:
                            final_stores = stores_query_selector["All"]
                        elif "Only London" in selected_stores:
                            final_stores = stores_query_selector["Only London"]
                        elif "Only Outside London" in selected_stores:
                            final_stores = stores_query_selector["Only Outside London"]
                        else:
                            # finally else covers any user selected mix of stores,
                            # apply map with lambda function to place apostrophes around each item in the iterable e.g. 'London Soho' 
                            # if all, only london, and only outside london are removed this is how the query would be created, clean one liner
                            final_stores = "AND store_name = " + " OR store_name = ".join(map((lambda a: f"'{a}'"), selected_stores))
        else:
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
        
        st.markdown(f"""###### :calendar: Selected Date : {dateme} """)
        # PORTFOLIO 
        if dev_mode:
            with st.expander("Semi-Complex Ternary Statement"):
                with st.echo():
                    # ternary statement to create display string, includes multiple replace methods followed by slice notation

                    # for display, create a display string unless the query has length that is the max length (for the query), which means it's "All"
                    # done because we dont want "Uppingham or Longridge or Chesterfield or..."
                    selected_stores_display = final_stores.replace("'","").replace("OR store_name =","or")[16:] if len(final_stores) < 149 else "All"
        else:
            selected_stores_display = final_stores.replace("'","").replace("OR store_name =","or")[16:] if len(final_stores) < 149 else "All"
        
        st.markdown(f"""###### :coffee: Selected Stores : {selected_stores_display} """)
        st.write("##")

        # ---- for st.metric header widget ----
        # PORTFOLIO 
        if dev_mode:
            with st.expander("See The Queries"):
                with st.echo():
                    # dynamic queries based on user inputs, try changing the date or stores to see updated queries
                    metricVals = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                            SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{dateme}' {final_stores};")

                    day_before = run_query(f"SELECT DATE(DATEADD(day, -1,'{dateme}'))")
                    day_before = day_before[0][0]

                    metricDeltas = run_query(f"SELECT SUM(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                            SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM redshift_bizinsights WHERE current_day = '{day_before}' {final_stores};")
        else:
            # this if else repetition is purely for showing queries and code for portfolio mode (dev mode)
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

        METRIC_ERROR = """
            Wild MISSINGNO Appeared!\n
            No Data for {} on {}\n
            ({})
            """

        show_metric = True

        metricErrorCol1, metricErrorCol2 = st.columns([2,1])
        if metricDeltaResults[0] == 0 and metricValueResults[0] == 0:
            metricErrorCol1.error(METRIC_ERROR.format(selected_stores_display, f"{day_before} OR {dateme}", "no selected or previous day available"))
            try:
                metricErrorCol2.image("imgs/Missingno.png")
            except FileNotFoundError:
                pass
            st.sidebar.info("Cause... Missing Numbers... Get it...")
            show_metric = False            
        elif metricDeltaResults[0] == 0:
            metricErrorCol1.error(METRIC_ERROR.format(selected_stores_display, day_before, "no delta (previous day) available"))
            try:
                metricErrorCol2.image("imgs/Missingno.png")
            except FileNotFoundError:
                pass
            st.sidebar.info("Cause... Missing Numbers... Get it...")
        elif metricValueResults[0] == 0:
            metricErrorCol1.error(METRIC_ERROR.format(selected_stores_display, dateme, "no selected day data available"))
            try:
                metricErrorCol2.image("imgs/Missingno.png")
            except FileNotFoundError:
                pass
            st.sidebar.info("Cause... Missing Numbers... Get it...")
        
        _, storeCol1, storeCol2, storeCol3, storeCol4, storeCol5, _ = st.columns(7)
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)

        def store_img_display(grab_store=False, store_to_grab="Chesterfield"):
            """ display stores as saturated img if not in search query, else full colour - uses dict switch with column object as value """
            store_dict = {"Uppingham":{"Col":storeCol1, "ImgClr":"imgs/coffee-shop-light-uppingham.png", "ImgStr":"imgs/coffee-shop-light-uppingham-saturated.png", "ImgSml":"imgs/cshop-small-uppingham.png"},
                                        "Longridge":{"Col":storeCol2, "ImgClr":"imgs/coffee-shop-light-longridge.png", "ImgStr":"imgs/coffee-shop-light-longridge-saturated.png", "ImgSml":"imgs/cshop-small-longridge.png"},
                                        "Chesterfield":{"Col":storeCol3, "ImgClr":"imgs/coffee-shop-light-chesterfield.png", "ImgStr":"imgs/coffee-shop-light-chesterfield-saturated.png", "ImgSml":"imgs/cshop-small-chesterfield.png"},
                                        "London Camden":{"Col":storeCol4, "ImgClr":"imgs/coffee-shop-light-london-camden.png", "ImgStr":"imgs/coffee-shop-light-london-camden-saturated.png", "ImgSml":"imgs/cshop-small-london-camden.png"},
                                        "London Soho":{"Col":storeCol5, "ImgClr":"imgs/coffee-shop-light-london-soho.png", "ImgStr":"imgs/coffee-shop-light-london-soho-saturated.png", "ImgSml":"imgs/cshop-small-london-soho.png"},
                                        }
            if grab_store:
                # if given parameters its because we just want to quickly grab one image, has less computation so put first in the if statement
                # returns img path
                return(store_dict[store_to_grab]["ImgSml"])
            else:
                store_list = ['Uppingham', 'Longridge', 'Chesterfield', 'London Camden', 'London Soho']
                for store_name in store_list:
                    if store_name in final_stores:
                        try:
                            store_dict[store_name]["Col"].image(store_dict[store_name]["ImgClr"])
                        except FileNotFoundError:
                            print("")
                    else:
                        try:
                            store_dict[store_name]["Col"].image(store_dict[store_name]["ImgStr"])
                        except FileNotFoundError:
                            print("")

        store_img_display()

        if show_metric:
            # note delta can be can be off, normal, or inverse (delta = current days value - previous days value)
            col1.metric(label="Total Revenue", value=f"${metric_tot_rev_val:.2f}", delta=f"${metric_tot_rev_delta:.2f}", delta_color="normal")
            col2.metric(label="Avg Spend", value=f"${metric_avg_spend_val:.2f}", delta=f"${metric_avg_spend_delta:.2f}", delta_color="normal")
            col3.metric(label="Total Customers", value=metric_tot_cust_val, delta=metric_tot_cust_delta, delta_color="normal") 
            col4.metric(label="Total Coffees Sold", value=metric_tot_cofs_val, delta=metric_tot_cofs_delta, delta_color="normal")

        st.write("---")

    st.write("##")



    # ---- New Section - Revenue Breakdown ----

    # DATE SELECTER container
    with st.container():
        st.write("##")
        st.markdown("### Store Revenue Breakdown")
  
        # store select and img print
        st.write("##")
        stores_list = ['Chesterfield', 'Uppingham', 'Longridge', 'London Camden', 'London Soho'] 
        dashboardRevStore1, dashboardRevStore2, dashboardRevStore3  = st.columns([1,2,2])
        with dashboardRevStore2:
            store_selector = st.selectbox("Choose The Store", options=stores_list, index=0, key="dashrevstore") 
        with dashboardRevStore1:
            try:
                dashRevStore_img = store_img_display(True, store_selector)
                st.image(dashRevStore_img)
            except FileNotFoundError:
                print("FileNotFoundError")

        # get revenue based data from db for given store
        try:
            # random bug, throws an error but works fine when page re-runs so try accept just to force to run twice idk why
            store_alltime_rev = db.get_stores_breakdown_revenue_via_bizi(store_selector, "alltime")
        except AttributeError:
            store_alltime_rev = db.get_stores_breakdown_revenue_via_bizi(store_selector, "alltime")

        storedates_alltime_rev = db.get_stores_breakdown_revenue_via_bizi(store_selector, "alltimedates")
        # get total available days for completeness, is dynamic so takes account all given days in db
        just_total_days_all_stores = db.get_stores_breakdown_revenue_via_bizi(store_selector, "justdays")

        just_store_dates_list = []
        dont_print = [just_store_dates_list.append(storedate[1]) for storedate in storedates_alltime_rev]
        with dashboardRevStore3:
            just_store_dates_list = sorted(just_store_dates_list)
            stores_dates = st.selectbox("Dates With Available Data (Not Selectable)", options=just_store_dates_list, index=0, key="dashdatesstore") 

        datadays_for_store = len(just_store_dates_list)
        first_store_date = just_store_dates_list[0]
        last_store_date = just_store_dates_list[-1]

        st.write("##")
        st.write("---")

        # new basic metric setup
        dashRevMetricCol1, dashRevMetricCol2, dashRevMetricCol3, dashRevMetricCol4 = st.columns(4)

        # btw surely need some validation here 
        dashRevMetricCol1.metric(label="All Time Revenue", value=f"${store_alltime_rev:.2f}")
        dashRevMetricCol2.metric(label="Avg Daily Revenue", value=f"${(store_alltime_rev / datadays_for_store):.2f}")
        dashRevMetricCol3.metric(label="Days of Data", value=f"{datadays_for_store}")
        dashRevMetricCol4.metric(label="Completeness [Days]", value=f"{((datadays_for_store/just_total_days_all_stores) * 100):.1f}%")

        st.write("---")
        st.write("##")


        # ---- ANALYSIS TOGGLE ----
        _, userCompareCol, _ = st.columns([2,2,2])
        with userCompareCol:
            userCompareSelect = st.radio(label="Choose Analysis Type", options=["Days of The Week", "Compare 2 Dates"], horizontal=True)
            st.write("##")


        # ---- COMPARE 2 DATES ----
        if userCompareSelect == "Compare 2 Dates":

            dashboardRevDate1, dashboardRevDate2 = st.columns(2)
            with dashboardRevDate1:
                user_start_date = st.date_input("What Start Date?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate, key="dashrevdate1")  
            with dashboardRevDate2:
                user_end_date = st.date_input("What End Date?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate, key="dashrevdate2") 
                
            #TODO - function if start date after end date (and else validation)    
            #def is_start_before_end():
                # NOT LIKE THIS THO - NEED AS INT DUH! - skip validate part for now anyways
                #print(f"{user_start_date = }")
                #print(f"{user_end_date = }")
                #daydiff = run_query(f"SELECT TO_DATE(DATEADD(day, {user_start_date}, '{user_end_date}'))")
                #print(f"{daydiff = }")

            st.write("---")


        # ---- DAYS OF THE WEEK ----
        elif userCompareSelect == "Days of The Week":

            final_week_of_year_list = [] 
            just_week_of_year_list = db.get_stores_breakdown_revenue_via_bizi(store_selector, "weekofyear")
            just_week_of_year_list = sorted(just_week_of_year_list)

            dont_print_2 = [final_week_of_year_list.append(weeknumb[0]) for weeknumb in just_week_of_year_list]

            #_, weekBreakdownCol1, weekBreakdownCol2 = st.columns([1,2,1])
            weekBreakdownCol1, weekBreakdownCol2 = st.columns([2,2])
            weeknumberselect = weekBreakdownCol1.selectbox(label="Choose A Week", options=final_week_of_year_list)  

            st.write("---")
            st.write("##")

            # get each day in loop starting at monday for the given week number
            st.write("")
            weekBreakdownDict = {}
            daynumb_dayname_dict = {1:"Monday",2:"Tuesday",3:"Wednesday",4:"Thursday",5:"Friday",6:"Saturday",7:"Sunday"}
            for i in range(1,8):
                data_for_day = run_query(f"SELECT * FROM redshift_bizinsights WHERE WEEKOFYEAR(current_day) = {weeknumberselect} AND DAYOFWEEKISO(current_day) = {i} AND store_name = '{store_selector}'")
                weekBreakdownDict[daynumb_dayname_dict[i]] = list(data_for_day)

            # calculate the first day of the week based on the other given dates and days info
            # portfolio this?!
            first_day_bool = False
            first_day = ""
            first_day_day_diff = 0
            for i, (day, info) in enumerate(weekBreakdownDict.items()):
                if first_day_bool == False:
                    try:
                        #print(info[0][4])
                        #print(i)
                        first_day_day_diff = i
                        first_day = info[0][4]
                        first_day_bool = True
                    except IndexError:
                        pass

            actual_first_day = run_query(f"SELECT TO_DATE(DATEADD(day, {-first_day_day_diff}, '{first_day}'))")
            # print(actual_first_day[0][0])
            weekBreakdownCol1.markdown(f"#### Week Commencing : {actual_first_day[0][0]}")

            # to display 
            days_available = []
            days_available_count = 0
            # for pasting ticks to calendar img
            week_array = []
            for i in range(1,8):
                try:
                    days_available.append(f"{daynumb_dayname_dict[i]} - Available [{weekBreakdownDict[daynumb_dayname_dict[i]][0][4]}]")
                    days_available_count += 1
                    week_array.append(True)
                except IndexError:
                    days_available.append(f"{daynumb_dayname_dict[i]} - No Data")
                    week_array.append(False)    

            # should cache artist prints btw as will be atleast somewhat computationally expensive
            june_start_weeknumb = 22
            highlight_week = weeknumberselect - june_start_weeknumb
            calendar_highlight = arty.highlight_calendar(highlight_week, weeknumberselect, week_array)
            weekBreakdownCol2.image(calendar_highlight)         

            # FIXME
            # can do a super basic html component here to remove any gap
            weekBreakdownCol1.markdown(f"##### {days_available_count} of 7 Days Available")
            weekBreakdownCol1.markdown(f"###### {((days_available_count/7)*100):.2f}% Availability")
            dont_print_3 = [weekBreakdownCol1.write(days_available[i]) for i in range(0,7)] # but it does actually print (is temp anyways)


            # f strings to fix decimal places and add currency! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< 
            # obvs can add more shit from the dict too 
            # obvs need lil title and date starting n shit 
            # then between 2 days 
            # then for a month or b month 
            # then done, could tidy but nah do later just move on to finish up whatelse (other minor charts n shit) 
            # for sure correlations n shit! 

            #FIXME
            # ALSO CONSIDER USE PREVIOUS DICT COL FUNCTION IDEA FOR THIS TOO?! 

            # OMG SO MUCH THIS, LITTLE IMG/COLOUR/HEAT/SPEEDO BARS THAT SHOW HOW WELL PERFOMING VS OTHERS FOR THE WEEK!!!!


            st.markdown("#### Weekly Breakdown")
            st.write("##")
            monCol, tueCol, wedCol, thuCol, friCol, satCol, sunCol = st.columns(7)
            # Monday 
            monCol.markdown("##### Monday")
            try:
                monCol.markdown(f"{weekBreakdownDict['Monday'][0][4]}")
                monCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Monday'][0][0]):.2f}")
                monCol.write("##")
                monCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Monday'][0][1]):.2f}")
                monCol.write("##")
                monCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Monday'][0][2])}")
                monCol.write("##")
                monCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Monday'][0][3])}")                
            except IndexError:
                monCol.write("-")
                monCol.metric(label="Revenue", value="N/A")
                monCol.write("##")
                monCol.metric(label="Avg Customer Spend", value="N/A")
                monCol.write("##")
                monCol.metric(label="Total Customers", value="N/A")
                monCol.write("##")
                monCol.metric(label="Coffees Sold", value="N/A")                
            # Tuesday
            tueCol.markdown("##### Tuesday")
            try:
                tueCol.markdown(f"{weekBreakdownDict['Tuesday'][0][4]}")
                tueCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Tuesday'][0][0]):.2f}")
                tueCol.write("##")
                tueCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Tuesday'][0][1]):.2f}")
                tueCol.write("##")
                tueCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Tuesday'][0][2])}")      
                tueCol.write("##")
                tueCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Tuesday'][0][3])}")                               
            except IndexError:
                tueCol.write("-")
                tueCol.metric(label="Revenue", value="N/A")
                tueCol.write("##")
                tueCol.metric(label="Avg Customer Spend", value="N/A")
                tueCol.write("##")
                tueCol.metric(label="Total Customers", value="N/A")
                tueCol.write("##")
                tueCol.metric(label="Coffees Sold", value="N/A")                
            # Wednesday
            wedCol.markdown("##### Wednesday")
            try:
                wedCol.markdown(f"{weekBreakdownDict['Wednesday'][0][4]}")
                wedCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Wednesday'][0][0]):.2f}") 
                wedCol.write("##")
                wedCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Wednesday'][0][1]):.2f}") 
                wedCol.write("##")
                wedCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Wednesday'][0][2])}")       
                wedCol.write("##")
                wedCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Wednesday'][0][3])}")                            
            except IndexError:
                wedCol.write("-")
                wedCol.metric(label="Revenue", value="N/A")
                wedCol.write("##")
                wedCol.metric(label="Avg Customer Spend", value="N/A")
                wedCol.write("##")
                wedCol.metric(label="Total Customers", value="N/A")     
                wedCol.write("##")
                wedCol.metric(label="Coffees Sold", value="N/A")                              
            # Thursday
            thuCol.markdown("##### Thursday")
            try:
                thuCol.markdown(f"{weekBreakdownDict['Thursday'][0][4]}")
                thuCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Thursday'][0][0]):.2f}")
                thuCol.write("##")
                thuCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Thursday'][0][1]):.2f}")
                thuCol.write("##")
                thuCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Thursday'][0][2])}")           
                thuCol.write("##")
                thuCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Thursday'][0][3])}")                       
            except IndexError:
                thuCol.write("-")
                thuCol.metric(label="Revenue", value="N/A")
                thuCol.write("##")
                thuCol.metric(label="Avg Customer Spend", value="N/A")
                thuCol.write("##")
                thuCol.metric(label="Total Customers", value="N/A")     
                thuCol.write("##")
                thuCol.metric(label="Coffees Sold", value="N/A")                                
            # Friday
            friCol.markdown("##### Friday")
            try:
                friCol.markdown(f"{weekBreakdownDict['Friday'][0][4]}")
                friCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Friday'][0][0]):.2f}")
                friCol.write("##")
                friCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Friday'][0][1]):.2f}")
                friCol.write("##")
                friCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Friday'][0][2])}")     
                friCol.write("##")
                friCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Friday'][0][3])}")                              
            except IndexError:
                friCol.write("-")
                friCol.metric(label="Revenue", value="N/A")
                friCol.write("##")
                friCol.metric(label="Avg Customer Spend", value="N/A")
                friCol.write("##")
                friCol.metric(label="Total Customers", value="N/A")                     
                friCol.write("##")
                friCol.metric(label="Coffees Sold", value="N/A")                                
            # Saturday
            satCol.markdown("##### Saturday")
            try:
                satCol.markdown(f"{weekBreakdownDict['Saturday'][0][4]}")
                satCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Saturday'][0][0]):.2f}")
                satCol.write("##")
                satCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Saturday'][0][1]):.2f}")
                satCol.write("##")
                satCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Saturday'][0][2])}")
                satCol.write("##")
                satCol.metric(label="Coffees Sold", value=f"{int(weekBreakdownDict['Saturday'][0][3])}")                
            except IndexError:
                satCol.write("-")
                satCol.metric(label="Revenue", value="N/A")
                satCol.write("##")
                satCol.metric(label="Avg Customer Spend", value="N/A")
                satCol.write("##")
                satCol.metric(label="Total Customers", value="N/A")       
                satCol.write("##")
                satCol.metric(label="Coffees Solid", value="N/A")          
            # Sunday
            sunCol.markdown("##### Sunday")
            try:
                sunCol.markdown(f"{weekBreakdownDict['Sunday'][0][4]}")
                sunCol.metric(label="Revenue", value=f"${float(weekBreakdownDict['Sunday'][0][0]):.2f}")
                sunCol.write("##")
                sunCol.metric(label="Avg Customer Spend", value=f"${float(weekBreakdownDict['Sunday'][0][1]):.2f}")
                sunCol.write("##")
                sunCol.metric(label="Total Customers", value=f"{int(weekBreakdownDict['Sunday'][0][2])}")   
                sunCol.write("##")
                sunCol.metric(label="Coffees Solid", value=f"{int(weekBreakdownDict['Sunday'][0][3])}")                              
            except IndexError:
                sunCol.write("-")
                sunCol.metric(label="Revenue", value="N/A") 
                sunCol.write("##")
                sunCol.metric(label="Avg Customer Spend", value="N/A")
                sunCol.write("##")
                sunCol.metric(label="Total Customers", value="N/A")           
                sunCol.write("##")
                sunCol.metric(label="Coffees Solid", value="N/A")                                        

            #print(weekBreakdownDict)

            # PUT AVG SPEND AND THE REST IN THERE OR SECTION OUT - TEST TO SEE CAUSE HAVE TO CONSIDER FORMATTING FOR N/A (should be fine tbf?)

        # NEXT <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # then ig quickly implement between 2 days, month



    # AITE SO LETS DO REVENUE BETWEEN DATES WITH OPTION FOR WEEK AND MONTH HERE 
    # - then maybe find some lil revenue specific extras to stick on top idk

    # ok so first its a store selector obvs
    # then you see all time regardless with a toggle for between dates (on that only for now ig) or for a full month
    # then below that is a week view and you can then select week by week from here
    # compare 2 stores might be nice too but could save for sumnt else tbf
    # then we'll explore more revenue breakdown stuff here too






# driver
try:
    run()
except snowflake.connector.errors.ProgrammingError:
    # testing error handling for app losing connection, rerun connection singleton, initialise connection, then run web app
    db.init_connection()
    conn = db.init_connection()
    run()

