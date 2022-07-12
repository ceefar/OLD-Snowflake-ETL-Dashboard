# artist.py

# ---- notes ----

# 1. nothing specific as of starting module


# ---- imports ----

# for image manipulation
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ---- main artist functions ----

# ---- store menus ----

def draw_dynamic_store_menu(imgname:str, listItems:list, listTitle:str) -> str:
    """ takes final name you want to give the image, a list of menu items, and the title (store name) and returns path to created menu image """

    # personal notes
    #  - would love to add price and maybe better formatting for flavours, requires proper bg image tho
    #  - would love to add in dynamic user inputs in some way but leaving as is for now
    #  - what really should do for listitems is store each listitems length and i, then match up longest list items with shortest 

    # path for the final image
    imgpath = f'imgs/menu_{imgname}'

    # base bg dimensions
    width = 360
    height = 255 

    # define font/s 
    font = ImageFont.truetype("imgs/Pacifico-Regular.ttf", size=8) 
    fontTitle = ImageFont.truetype("imgs/Sacramento-Regular.ttf", size=28) 


    # ---- title ----

    # open new img object of our chalkboard menu background
    img = Image.open('imgs/chalkboard_1.jpg')
    # setup base object from original bg img and open it for drawing 
    imgDraw = ImageDraw.Draw(img)

    # configure the title text position, and grab its dimensions based on its font incase we need them
    shopTitle = listTitle
    titleWidth, titleHeight = imgDraw.textsize(shopTitle, font=fontTitle) # textsize is going to be depreciated soon btw
    # centralise based on title width 
    xTitlePos = ((width-titleWidth) - titleWidth) / 2
    yTitlePos = 50

    # draw the title on the bg img
    imgDraw.text((xTitlePos, yTitlePos), shopTitle, font=fontTitle, fill="#FBF7F5") 

    # save the result
    img.save(imgpath)



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
        
    # should add personal watermark here too btw
    # could also add text like "sorry for unavailable items" if any valid boolean flag was raised

    return(imgpath)



def highlight_calendar(weeknumb:int) -> str:
    """ write me pls ceef """

    # path for the final image
    imgpath = f'imgs/test_june_{weeknumb}.png'

    # open img object
    img = Image.open('imgs/Calendar-2022-June.png')
    # setup base object from original bg img and open it for drawing 
    imgDraw = ImageDraw.Draw(img)

    # save the bg before adding rectangle highlight
    img.save(imgpath)

    # ---- start rectangle ----

    # create new draw object with transparency option
    img1 = ImageDraw.Draw(img, "RGBA")

    nudgeVar = 5
    incVar = 90
    n1 = 930 # doesnt change (assuming width)
    n2 = 220
    n3 = 30 # doesnt change (assuming height)
    n4 = 127

    if weeknumb == 1:
        n4 += (incVar * 2) + nudgeVar
    elif weeknumb == 2:
        n2 += incVar
        n4 += (incVar*3) + (nudgeVar*2)
    elif weeknumb == 3:
        n2 += (incVar * 2) + nudgeVar
        n4 += (incVar * 4) + (nudgeVar*2)
    elif weeknumb == 4:    
        n2 += (incVar * 3) + (nudgeVar*2)
        n4 += (incVar * 5) + (nudgeVar*2)

    # resulting position x dimensions
    # [930, 220, 30, 127]
    # [930, 220, 30, 307]
    # [930, 310, 30, 397]
    # [930, 400, 30, 487]
    # [930, 490, 30, 577]

    # semi-dynamically set the rectangle vars
    rectPos = [n1, n2, n3, n4]
    # draw the rectangle with transparency
    img1.rectangle(rectPos, fill=(255, 0, 0, 55))

    # crop the bottom off the final img - left pos of crop, top pos of crop, width of final img, height of final img
    img = img.crop((0, 0, 960, 600))

    img.save(imgpath)
    return(imgpath)


