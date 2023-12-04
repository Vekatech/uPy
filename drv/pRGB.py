from machine import LCD
import framebuf
import lvgl as lv
import lv_utils

SuppRes = [
    (480, 272)
]

class pRGB(framebuf.FrameBuffer):

    def __init__(self, res=SuppRes[0]):
        if res not in SuppRes:
            raise ValueError('Unsupported resolution %s; the driver supports: %s.'%(str(res),', '.join(str(r) for r in suppRes)))

        self.width = res[0]   #480
        self.height = res[1]  #272
        self.display = LCD()
        super().__init__(self.display, self.width, self.height, framebuf.RGB565)
        self.display.init()
        self.display.start()

class pRGB_lvgl(object):
    '''LVGL wrapper for paralel RGB LCD, not to be instantiated directly.

    * creates and registers LVGL display driver;
    * allocates buffers (single-buffered by default);
    * sets the driver callback to the disp_drv_flush_cb method.

    '''
    def disp_drv_flush_cb(self,disp_drv,area,color):
        # print(f"({area.x1},{area.y1}..{area.x2},{area.y2})")
        w = area.x2-area.x1+1
        h = area.y2-area.y1+1

        # blit in background
        self.blit(framebuf.FrameBuffer(color.__dereference__(w*h*lv.color_t.__SIZE__), w, h, framebuf.RGB565), area.x1, area.y1)
        self.disp_drv.flush_ready()

    def touch_drv_read_cb(self,touch_drv,data):
        self.points = self.display.touched()
        if(self.points > 0):
            dots = self.display.touches()
            data.point = lv.point_t({'x': dots[self.points-1][0], 'y': dots[self.points-1][1]})
            data.state = lv.INDEV_STATE.PRESSED
        else:
            data.state = lv.INDEV_STATE.RELEASED

    def __init__(self,doublebuffer=False,factor=10):
        if hasattr(lv, 'COLOR_DEPTH'):
            if lv.COLOR_DEPTH!=16: raise RuntimeError(f'LVGL *must* be compiled with LV_COLOR_DEPTH=16 (currently LV_COLOR_DEPTH={lv.COLOR_DEPTH}.')
        
        bufSize=(self.width*self.height*lv.color_t.__SIZE__)//factor

        if not lv.is_initialized(): lv.init()
        # create event loop if not yet present
        if not lv_utils.event_loop.is_running(): self.event_loop=lv_utils.event_loop()

        # attach all to self to avoid objects' refcount dropping to zero when the scope is exited
        if hasattr(lv, 'disp_create'):
            self.disp_drv = lv.disp_create(self.width, self.height)
        else:
            self.disp_drv = lv.disp_drv_t()
            self.disp_drv.init()
            self.disp_drv.hor_res = self.width
            self.disp_drv.ver_res = self.height

        if hasattr(self.disp_drv, 'set_flush_cb'):
            self.disp_drv.set_flush_cb(self.disp_drv_flush_cb)
        else:
            self.disp_drv.flush_cb = self.disp_drv_flush_cb

        if hasattr(self.disp_drv, 'set_draw_buffers'):
            self.disp_drv.set_draw_buffers(bytearray(bufSize), bytearray(bufSize) if doublebuffer else None, bufSize, lv.DISP_RENDER_MODE.PARTIAL)
        else:
            self.disp_drv.draw_buf = lv.disp_draw_buf_t()
            self.disp_drv.draw_buf.init(bytearray(bufSize), bytearray(bufSize) if doublebuffer else None, bufSize)
            self.disp_drv.register()

        if hasattr(self.disp_drv, 'set_color_format'):
            self.disp_drv.set_color_format(lv.COLOR_FORMAT.RGB565)

        

        self.points = 0
        if hasattr(lv, 'indev_create'):
            self.indev_drv = lv.indev_create()
        else:
            self.indev_drv = lv.indev_drv_t()
            self.indev_drv.init()

        if hasattr(self.indev_drv, 'set_type'):
            self.indev_drv.set_type(lv.INDEV_TYPE.POINTER)
        else:
            self.indev_drv.type = lv.INDEV_TYPE.POINTER

        if hasattr(self.indev_drv, 'set_read_cb'):
            self.indev_drv.set_read_cb(self.touch_drv_read_cb)
        else:
            self.indev_drv.read_cb = self.touch_drv_read_cb
            self.indev_drv.register()

class RGB(pRGB,pRGB_lvgl):
    def __init__(self,res=SuppRes[0],doublebuffer=False,factor=10,**kw):
        '''See :obj:`St77xx_hw` for the meaning of the parameters.'''
        pRGB.__init__(self,res)
        pRGB_lvgl.__init__(self,doublebuffer,factor)