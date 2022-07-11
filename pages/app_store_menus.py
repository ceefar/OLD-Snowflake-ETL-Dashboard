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


# ---- for portfolio display

ARTIST_1 = """

    # code snippet from 
    def draw_dynamic_store_menu(imgname:str, listItems:list, listTitle:str) -> str:

    # ---- listed menu items ----

    # how many menu items there are
    amountOfListItems = len(listItems)
    #print(f"{amountOfListItems = }")

    # var used for creating new spacing for each line
    last_item_y_pos = 0
    # var used for cropping & 2nd column x positioning, need to know what is the longest line on the page
    longest_list_item = 0
    # vars for setting list items x position in second loop (dont want this to change)
    secondloop = False
    longest_li_second_loop = longest_list_item

    # runs (draws) for each item in the list
    for i, item in enumerate(listItems):
        
        # boolean flag for if need to add strikethrough
        strikme = False

        # if had the text based flag, remove it (for accurate sizing), then set the above boolean
        if item[0] == "!":
            item = item[1:]
            strikme = True

        # temporary slice long lines if there are two columns on the page since could break formatting
        if len(item) > 28 and amountOfListItems > 6:
            item = item[:28]

        # setup base object
        imgDraw = ImageDraw.Draw(img)

        # to set the new x pos for the second loop once and not have it change
        if amountOfListItems > 6 and i > 5 and secondloop == False:
            longest_li_second_loop = longest_list_item + 5
            secondloop = True
            # print(f"{longest_list_item = }")

        # configure list items x position, and grab its dimensions based on its font incase we need them
        listItem = item
        liWidth, liHeight = imgDraw.textsize(listItem, font=font)
        if i <= 5:
            xLiTextPos = 20
        else:
            xLiTextPos = longest_li_second_loop + 30
        #print(f"{xLiTextPos = }")

        # if list item is the longest save it outside of loop
        if liWidth > longest_list_item:
            longest_list_item = liWidth
        
        # should reset for the second loop
        if i == 6:
            last_item_y_pos = 0

        # if first iteration only
        if last_item_y_pos == 0:
            # slightly different as need to set the first position as it is the hinge for the remaining list items
            last_item_y_pos = yTitlePos + 25.5 
            # print(f"{last_item_y_pos = }") 

        # after this every line is just added a set amount (dont use liHeight as this changes duhhh)
        yLiTextPos = last_item_y_pos + 22.5
        last_item_y_pos = yLiTextPos
        # print(f"{last_item_y_pos = }")

        # draw the list item text
        imgDraw.text((xLiTextPos, yLiTextPos), listItem, font=font, fill="#FBF7F5") # 191970 midnight blue

        # draw the strikethrough if valid
        if strikme == True:
            img1 = ImageDraw.Draw(img)
            img1.rectangle([xLiTextPos, yLiTextPos+7, xLiTextPos+liWidth,  yLiTextPos+8], fill="#DC143C")

        # save the result
        img.save(imgpath)
"""


# ---- main web app ----

# ---- sidebar ----

# might not use but leaving just incase
with st.sidebar:
    st.write("##")
    st.markdown("#### Portfolio Mode")
    st.write("To view live code snippets")
    devmode2 = st.checkbox("Portfolio Mode", key="devmode2-menus")

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
        
        st.markdown("#### Create Store Menu - Set Item Availability")
        st.write("##")

        # get every valid unique combination of item, size and flavour, returned as tuple for the selected store only
        get_menu = run_query(f"SELECT DISTINCT i.item_name, i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector}'")

        # for adding checkboxes next to menu items, 2 column display (so matches the menu print out for visual clarity)
        menuitemCol1, itemcheckboxCol1, _, menuitemCol2, itemcheckboxCol2 = st.columns([2,1,1,2,1])

        

        #FIXME : This will look sooo much better if the image is on the right of the checkboxes duh



        if devmode2:
            st.write("##")
            with st.expander("Creating Menu Images - Part 1"):
                with st.echo():

                    # loop each item in the menu, print out checkboxes, create final list of menu items for artist to print
                    final_menu = []
                    for i, item in enumerate(get_menu):
                        
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

        else:
            
            final_menu = []
            for i, item in enumerate(get_menu):
                final_item = []
                dont_print = [final_item.append(subitem) for subitem in item if subitem is not None]
                menu_item = (" ".join(final_item))
                menu_item = menu_item.title().strip()
                itemBoxKey = f"{store_selector}_{menu_item}"

                if i > 5:
                    menuitemCol2.markdown(f"##### {menu_item}")
                    if itemcheckboxCol2.checkbox(label="Unavailable", key=itemBoxKey):
                        menu_item = f"!{menu_item}"
                else:
                    menuitemCol1.markdown(f"##### {menu_item}")
                    if itemcheckboxCol1.checkbox(label="Unavailable", key=itemBoxKey):
                        menu_item = f"!{menu_item}"
                final_menu.append(menu_item)

        st.write("##")
        st.write("---") 
        st.write("##")

        st.markdown("#### Your Menu Image")
        st.write("##")

        # create and print the image to web app, format of filename = menu_StoreName.png, filepath = imgs/ 
        store_menu_img = arty.draw_dynamic_store_menu(f"{store_selector}.png", final_menu, store_selector)
        st.image(store_menu_img)
        
        if devmode2:
            st.write("##")
            with st.expander("Creating Menu Images - Part 2"):
                st.write("Partial Code From My External Module Artist.py, Which Uses PIL (pillow)")
                st.code(ARTIST_1, language="python")
            

        st.write("##")
        st.write("---") 

        item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector}", key="item_selector_1", options=final_menu, index=0) 

        st.write("##")
        st.write("---") 






run()