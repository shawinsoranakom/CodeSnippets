def wkt(self):
        "Return the WKT representation of the Geometry."
        # For backward compatibility, export old-style 99-402 extended
        # dimension types when geometry does not have an M dimension.
        # https://gdal.org/api/vector_c_api.html#_CPPv417OGR_G_ExportToWkt12OGRGeometryHPPc
        to_wkt = capi.to_iso_wkt if self.is_measured else capi.to_wkt
        return to_wkt(self.ptr, byref(c_char_p()))