def test_lookup_in_fields(self):
        s = SelfRef.objects.create()
        msg = (
            'Found "__" in fields argument. Relations and transforms are not allowed '
            "in fields."
        )
        with self.assertRaisesMessage(ValueError, msg):
            s.refresh_from_db(fields=["foo__bar"])