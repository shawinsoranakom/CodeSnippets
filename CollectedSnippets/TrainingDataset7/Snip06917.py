def __init__(self, feat, index):
        """
        Initialize on the feature object and the integer index of
        the field within the feature.
        """
        # Setting the feature pointer and index.
        self._feat = feat
        self._index = index

        # Getting the pointer for this field.
        fld_ptr = capi.get_feat_field_defn(feat.ptr, index)
        if not fld_ptr:
            raise GDALException("Cannot create OGR Field, invalid pointer given.")
        self.ptr = fld_ptr

        # Setting the class depending upon the OGR Field Type (OFT)
        self.__class__ = OGRFieldTypes[self.type]