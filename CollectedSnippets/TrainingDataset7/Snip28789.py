def test_string(self):
        # Clear cached property.
        Relation._meta.__dict__.pop("verbose_name_raw", None)
        self.assertEqual(Relation._meta.verbose_name_raw, "relation")