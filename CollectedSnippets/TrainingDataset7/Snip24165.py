def geometry(self, obj):
        # This should attach a <georss:box> element for the extent of
        # the cities in the database. This tuple came from
        # calling `City.objects.aggregate(Extent())` -- we can't do that call
        # here because `Extent` is not implemented for MySQL/Oracle.
        return (-123.30, -41.32, 174.78, 48.46)