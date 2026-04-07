def test_gettext(self):
        Person._meta.__dict__.pop("verbose_name_raw", None)
        self.assertEqual(Person._meta.verbose_name_raw, "Person")