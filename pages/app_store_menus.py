# app_store_menus.py

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
# for drawing menus 
import artist as arty


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


# ---- page functions ----

# rip works in terminal but not pillow, leaving as may want in future
def strike(text):
    """ for adding basic strikethrough to text """
    result = ''
    try:
        for c in text:
            result = result + c + '\u0336'
        return(result)
    # in the case of simple type error return the original text instead
    except TypeError:
        return(text)


# ---- main web app ----

# ---- sidebar ----

# might not use but leaving just incase
with st.sidebar:
    st.write("##")
    st.markdown("#### Portfolio Mode")
    st.write("To view live code snippets")
    devmode = st.checkbox("Portfolio Mode")


def run():

    # BASE QUERIES queries & vars
    currentdate = run_query("SELECT DATE(GETDATE())")
    yesterdate = run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))")
    firstdate = run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")
    currentdate = currentdate[0][0]
    yesterdate = yesterdate[0][0]
    firstdate = firstdate[0][0]
    stores_list = ['Chesterfield', 'Uppingham', 'Longridge',  'London Camden', 'London Soho']

    # STORE MENUS artist
    with st.container():
        st.write(f"### :bulb: Title") 
        st.write("##### Subtitle")
        st.write("Short blurb text") # because they are all favoured so really theres 15 not 3
        st.write("##")
        
        # store selector
        store_selector = st.selectbox(label="Choose The Store", key="store_select_art_1", options=stores_list, index=0) 
        st.write("---") 
        st.write("##")
        
        # get every valid unique combination of item, size and flavour, returned as tuple for the selected store only
        get_menu = run_query(f"SELECT DISTINCT i.item_name, i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector}'")

        # for adding checkboxes next to menu items, 2 column display (so matches the menu print out for visual clarity)
        menuitemCol1, itemcheckboxCol1, _, menuitemCol2, itemcheckboxCol2 = st.columns([2,1,1,2,1])



        # TODO
        # FIXME
        # PORTFOLIO - ADD THIS TO DEV MODE 100!

        # loop each item in the menu, print out checkboxes, create final list of menu items for artist to print
        final_menu = []
        for i, item in enumerate(get_menu):
            
            # i guess the point of something like this would be to push to socials, or tbf various other possibilities
            
            final_item = []
            # remove any None types from the tuple returned from the query - None happens when an item has no flavour
            dont_print = [final_item.append(subitem) for subitem in item if subitem is not None]
            # join each element of iterable in to one string with spaces between (e.g Flavoured Latte + Vanilla, Flavoured Latte + Hazelnut)
            menu_item = (" ".join(final_item))
            # format slightly
            menu_item = menu_item.title().strip()

            # checkbox keys must be unqiue so creating from store name + menu item 
            # - in future could use alongside sessionstate to do more indepth things like activating an offer for examples
            itemBoxKey = f"{store_selector}_{menu_item}"

            # for right side items
            if i > 5:
                menuitemCol2.markdown(f"##### {menu_item}")
                if itemcheckboxCol2.checkbox(label="Unavailable", key=itemBoxKey):
                    # using ! as a flag to validate strikethrough in artist
                    menu_item = f"!{menu_item}"

            # for left side items
            else:
                menuitemCol1.markdown(f"##### {menu_item}")
                if itemcheckboxCol1.checkbox(label="Unavailable", key=itemBoxKey):
                    # using ! as a flag to validate strikethrough in artist
                    menu_item = f"!{menu_item}"

            # finally append item to a list for user selected store
            final_menu.append(menu_item)

        st.write("##")
        st.write("---") 
        st.write("##")

        # create and print the image to web app, format of filename = menu_StoreName.png, filepath = imgs/ 
        store_menu_img = arty.draw_dynamic_store_menu(f"{store_selector}.png", final_menu, store_selector)
        st.image(store_menu_img)

        st.write("##")
        st.write("---") 

        item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector}", key="item_selector_1", options=final_menu, index=0) 

        st.write("##")
        st.write("---") 






run()