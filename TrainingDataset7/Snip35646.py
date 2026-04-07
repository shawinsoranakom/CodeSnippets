def test_update_ordered_by_m2m_aggregation_annotation(self):
        msg = (
            "Cannot update when ordering by an aggregate: "
            "Count(Col(update_bar_m2m_foo, update.Bar_m2m_foo.foo))"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Bar.objects.annotate(m2m_count=Count("m2m_foo")).order_by(
                "m2m_count"
            ).update(x=2)