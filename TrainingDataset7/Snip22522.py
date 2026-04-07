def test_datefield_changed(self):
        format = "%d/%m/%Y"
        f = DateField(input_formats=[format])
        d = date(2007, 9, 17)
        self.assertFalse(f.has_changed(d, "17/09/2007"))