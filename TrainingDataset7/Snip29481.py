def test_array_agg_with_order_by_outer_ref(self):
        StatTestModel.objects.annotate(
            atm_ids=Subquery(
                AggregateTestModel.objects.annotate(
                    ids=ArrayAgg(
                        "id",
                        order_by=[OuterRef("int1")],
                    )
                ).values("ids")[:1]
            )
        )