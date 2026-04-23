def func(self):
        from django.contrib.gis.geos.prototypes.threadsafe import GEOSFunc

        func = GEOSFunc(self.func_name)
        func.argtypes = self.argtypes or []
        func.restype = self.restype
        if self.errcheck:
            func.errcheck = self.errcheck
        return func