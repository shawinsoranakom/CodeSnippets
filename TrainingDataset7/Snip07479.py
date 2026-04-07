def __init__(self):
        self.ptr = lgeos.GEOS_init_r()
        lgeos.GEOSContext_setNoticeHandler_r(self.ptr, notice_h)
        lgeos.GEOSContext_setErrorHandler_r(self.ptr, error_h)