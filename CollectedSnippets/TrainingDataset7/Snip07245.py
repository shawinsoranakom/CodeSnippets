def clone(self):
        "Clone this coordinate sequence."
        return GEOSCoordSeq(capi.cs_clone(self.ptr), self.hasz)