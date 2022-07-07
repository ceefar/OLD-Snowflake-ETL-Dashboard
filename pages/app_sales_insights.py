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
# cache this function?
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





    ###################################################################
    #                                                                 #
    #                                                                 #
    # BIG N0TE - GUNA WANT ECHO AND DEV MODE HERE LIKE FUCK BOIIIIII! #
    #                                                                 #
    #                                                                 #
    ###################################################################





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


