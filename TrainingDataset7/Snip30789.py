def test_primary_key(self):
        custom = CustomPk.objects.create(name="pk")
        null = Related.objects.create()
        notnull = Related.objects.create(custom=custom)
        self.assertSequenceEqual(
            Related.objects.filter(custom__isnull=False), [notnull]
        )
        self.assertSequenceEqual(Related.objects.filter(custom__isnull=True), [null])