def test_refresh_when_one_field_deferred(self):
        s = Secondary.objects.create()
        PrimaryOneToOne.objects.create(name="foo", value="bar", related=s)
        s = Secondary.objects.defer("first").get()
        p_before = s.primary_o2o
        s.refresh_from_db()
        self.assertIsNot(s.primary_o2o, p_before)