def validate(self):
        "Check to see if the given spatial reference is valid."
        capi.srs_validate(self.ptr)