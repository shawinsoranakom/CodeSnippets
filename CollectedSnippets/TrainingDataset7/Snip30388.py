def test_falsey_pk_value(self):
        order = Order.objects.create(pk=0, name="test")
        order.name = "updated"
        Order.objects.bulk_update([order], ["name"])
        order.refresh_from_db()
        self.assertEqual(order.name, "updated")