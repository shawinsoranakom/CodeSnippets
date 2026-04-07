def test_annotation_and_alias_filter_in_subquery(self):
        awarded_publishers_qs = (
            Publisher.objects.filter(num_awards__gt=4)
            .annotate(publisher_annotate=Value(1))
            .alias(publisher_alias=Value(1))
        )
        qs = Publisher.objects.filter(pk__in=awarded_publishers_qs)
        self.assertCountEqual(qs, [self.p3, self.p4])