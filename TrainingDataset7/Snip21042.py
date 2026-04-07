def test_refresh_not_loading_deferred_fields(self):
        s = Secondary.objects.create()
        rf = Primary.objects.create(name="foo", value="bar", related=s)
        rf2 = Primary.objects.only("related", "value").get()
        rf.name = "new foo"
        rf.value = "new bar"
        rf.save()
        with self.assertNumQueries(1):
            rf2.refresh_from_db()
            self.assertEqual(rf2.value, "new bar")
        with self.assertNumQueries(1):
            self.assertEqual(rf2.name, "new foo")