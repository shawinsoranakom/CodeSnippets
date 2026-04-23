def test_update_negated_f_conditional_annotation(self):
        DataPoint.objects.annotate(
            is_d2=Case(When(name="d2", then=True), default=False)
        ).update(is_active=~F("is_d2"))
        self.assertCountEqual(
            DataPoint.objects.values_list("name", "is_active"),
            [("d0", True), ("d2", False), ("d3", True)],
        )