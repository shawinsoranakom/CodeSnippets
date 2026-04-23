def wkb(self):
        "Return the WKB representation of the Geometry."
        if sys.byteorder == "little":
            byteorder = 1  # wkbNDR (from ogr_core.h)
        else:
            byteorder = 0  # wkbXDR
        sz = self.wkb_size
        # Creating the unsigned character buffer, and passing it in by
        # reference.
        buf = (c_ubyte * sz)()
        # For backward compatibility, export old-style 99-402 extended
        # dimension types when geometry does not have an M dimension.
        # https://gdal.org/api/vector_c_api.html#_CPPv417OGR_G_ExportToWkb12OGRGeometryH15OGRwkbByteOrderPh
        to_wkb = capi.to_iso_wkb if self.is_measured else capi.to_wkb
        to_wkb(self.ptr, byteorder, byref(buf))
        # Returning a buffer of the string at the pointer.
        return memoryview(string_at(buf, sz))