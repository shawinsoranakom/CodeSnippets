def wkb_size(self):
        "Return the size of the WKB buffer."
        return capi.get_wkbsize(self.ptr)