def fid(self):
        "Return the feature identifier."
        return capi.get_fid(self.ptr)