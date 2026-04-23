def test_field_verbose_name(self):
        m = VerboseNameField
        for i in range(1, 22):
            self.assertEqual(
                m._meta.get_field("field%d" % i).verbose_name, "verbose field%d" % i
            )

        self.assertEqual(m._meta.get_field("id").verbose_name, "verbose pk")