def test_disallowed_update_distinct_on(self):
        qs = Staff.objects.distinct("organisation").order_by("organisation")
        msg = "Cannot call update() after .distinct(*fields)."
        with self.assertRaisesMessage(TypeError, msg):
            qs.update(name="p4")