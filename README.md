# uPy
Libs & Drivers for micropython enabled VK boards

## Content :
Currently the list of micropython enabled **VK** boards is as follows :

- [VK-RA4W1](https://vekatech.com/VK-RA4W1_docs/brochures/VK-RA4W1%20Flyer%20R2.pdf) [#10595](https://github.com/micropython/micropython/pull/10595) ![Package](https://badgen.net/badge/status/pending%20for%20merge/orange?icon=git)
- [VK-RA6M3](https://vekatech.com/VK-RA6M3_docs/brochures/VK-RA6M3%20Flyer%20R2.pdf) [#10752](https://github.com/micropython/micropython/pull/10752) ![Package](https://badgen.net/badge/status/pending%20for%20merge/orange?icon=git)
- [VK-RA6M5](https://vekatech.com/VK-RA6M5_docs/brochures/VK-RA6M5%20Flyer%20R2.pdf) [#10943](https://github.com/micropython/micropython/pull/10943) ![Package](https://badgen.net/badge/status/pending%20for%20merge/orange?icon=git)

### Libs
- **Test >** this Lib tests the following peripheries of uPy VK boards:
  - **I<sup>2</sup>C** (expects slave to be connected on SDA & SCL )
    - Once `Test.py` & `ssd1306.py` are in **FS** of the board, you are ready to run it like so:
    ```python
    >>> import Test
    >>> Test.OLED()
    ```
  - **SPI** (expects slave to be connected on SCK, MOSI, & D7-D9 )
    - Once `Test.py` & `st7789.py` are in **FS** of the board, you are ready ti run it like so:
    ```python
    >>> import Test
    >>> Test.TFT()
    ```
### Drv
- **ssd1306 >** murcopython OLED driver (works with devices based on that particular controller, such as [SBC-OLED01](https://www.joy-it.net/en/products/SBC-OLED01))
- **st7789 >** micropython TFT driver (works with devices based on that particular controller, such as [SBC-LCD01](https://www.joy-it.net/en/products/SBC-LCD01))
