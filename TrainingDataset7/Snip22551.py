def test_email_regexp_for_performance(self):
        f = EmailField()
        # Check for runaway regex security problem. This will take a long time
        # if the security fix isn't in place.
        addr = "viewx3dtextx26qx3d@yahoo.comx26latlngx3d15854521645943074058"
        with self.assertRaisesMessage(ValidationError, "Enter a valid email address."):
            f.clean(addr)