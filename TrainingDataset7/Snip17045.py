def test_string_agg_order_by_is_not_supported(self):
        message = (
            "This database backend does not support specifying an order on aggregates."
        )
        with self.assertRaisesMessage(NotSupportedError, message):
            Store.objects.aggregate(
                stringagg=StringAgg(
                    "name",
                    delimiter=Value(";"),
                    order_by="original_opening",
                )
            )