def test_update_multiple_fields(self):
        """
        Multiple fields can be updated at once
        """
        resp = DataPoint.objects.filter(value="apple").update(
            value="fruit", another_value="peach"
        )
        self.assertEqual(resp, 1)
        d = DataPoint.objects.get(name="d0")
        self.assertEqual(d.value, "fruit")
        self.assertEqual(d.another_value, "peach")