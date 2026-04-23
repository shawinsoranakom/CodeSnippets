def __repr__(self):
        "Short-hand representation because WKT may be very large."
        return "<%s object at %s>" % (self.geom_type, hex(addressof(self.ptr)))