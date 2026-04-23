def test_appendlist(self):
        d = MultiValueDict()
        d.appendlist("name", "Adrian")
        d.appendlist("name", "Simon")
        self.assertEqual(d.getlist("name"), ["Adrian", "Simon"])