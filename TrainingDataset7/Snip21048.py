def test_only_select_related_raises_invalid_query(self):
        msg = (
            "Field Primary.related cannot be both deferred and traversed using "
            "select_related at the same time."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Primary.objects.only("name").select_related("related")[0]