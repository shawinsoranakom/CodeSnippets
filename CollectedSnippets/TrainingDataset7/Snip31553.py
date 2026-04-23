def test_unsupported_select_for_update_with_limit(self):
        msg = (
            "LIMIT/OFFSET is not supported with select_for_update on this database "
            "backend."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            with transaction.atomic():
                list(Person.objects.order_by("pk").select_for_update()[1:2])