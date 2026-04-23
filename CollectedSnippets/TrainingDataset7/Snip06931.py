def type(self):
        """
        GDAL uses OFTReals to represent OFTIntegers in created
        shapefiles -- forcing the type here since the underlying field
        type may actually be OFTReal.
        """
        return 0