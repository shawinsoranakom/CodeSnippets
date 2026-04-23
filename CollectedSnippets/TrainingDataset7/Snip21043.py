def test_custom_refresh_on_deferred_loading(self):
        s = Secondary.objects.create()
        rf = RefreshPrimaryProxy.objects.create(name="foo", value="bar", related=s)
        rf2 = RefreshPrimaryProxy.objects.only("related").get()
        rf.name = "new foo"
        rf.value = "new bar"
        rf.save()
        with self.assertNumQueries(1):
            # Customized refresh_from_db() reloads all deferred fields on
            # access of any of them.
            self.assertEqual(rf2.name, "new foo")
            self.assertEqual(rf2.value, "new bar")