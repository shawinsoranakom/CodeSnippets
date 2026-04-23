def test_aggregation_default_unsupported_by_count(self):
        msg = "Count does not allow default."
        with self.assertRaisesMessage(TypeError, msg):
            Count("age", default=0)