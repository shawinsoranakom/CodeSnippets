def test_ticket22023(self):
        with self.assertRaisesMessage(
            TypeError, "Cannot call only() after .values() or .values_list()"
        ):
            Valid.objects.values().only()

        with self.assertRaisesMessage(
            TypeError, "Cannot call defer() after .values() or .values_list()"
        ):
            Valid.objects.values().defer()