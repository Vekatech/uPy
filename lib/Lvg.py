from os import uname
from machine import SPI
from pRGB import lv, RGB as Pdrv
from st77xx import St7789 as STdrv

BRD = uname().machine

def TST():
    def slider_event_cb(e):
        if hasattr(e, 'get_target_obj'):
            slider = e.get_target_obj()
        else:
            slider = e.get_target()

        # Refresh the text
        label.set_text(str(slider.get_value()))

    scr = lv.scr_act()

    #scr.set_style_bg_color(lv.color_hex(0x00ff00), lv.PART.MAIN)

    # Create a white label, set its text and align it to the center
    label = lv.label(scr)
    label.set_text("Hello world")
    label.set_style_text_color(lv.color_hex(0x000000), lv.PART.MAIN)
    label.align(lv.ALIGN.CENTER, 0, 0)

    #
    # Create a slider and write its value on a label.
    #
    
    # Create a slider in the center of the display
    slider = lv.slider(scr)
    slider.set_width(200)                                               # Set the width
    #slider.set_pos(20, 180)
    slider.center()                                                    # Align to the center of the parent (screen)
    slider.align(lv.ALIGN.CENTER, 0, 70)
    if hasattr(slider, 'add_event'):
        slider.add_event(slider_event_cb, lv.EVENT.VALUE_CHANGED, None)  # Assign an event function
    else:
        slider.add_event_cb(slider_event_cb, lv.EVENT.VALUE_CHANGED, None)  # Assign an event function

    # Create a label above the slider
    label = lv.label(scr)
    label.set_text("0")
    label.align_to(slider, lv.ALIGN.OUT_TOP_MID, 0, -15)               # Align below the slider

if ("VK-RA6M5" in BRD):
    ch = 0
    lcd = STdrv(rot=0,res=(240,240),spi=SPI(ch, baudrate=40000000, polarity=1),rp2_dma=None,cs='D6',dc='D8',bl='D7',rst='D9',doublebuffer=False,factor=10)
    lcd.set_backlight(100)
elif "VK-RA6M3" in BRD:
    ch = 1
    lcd = Pdrv()
    #lcd = STdrv(rot=0,res=(240,240),spi=SPI(ch, baudrate=40000000, polarity=1),rp2_dma=None,cs='D5',dc='D8',bl='D6',rst='D9',doublebuffer=False,factor=10)
    #lcd.set_backlight(100)
else:
    ch = -1
