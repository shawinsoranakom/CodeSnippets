def test_actual_expiry(self):
        # The cookie backend doesn't handle non-default expiry dates, see
        # #19201
        super().test_actual_expiry()