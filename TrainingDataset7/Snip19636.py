def test_outer_ref_in_filtered_relation(self):
        msg = (
            "This queryset contains a reference to an outer query and may only be used "
            "in a subquery."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.assertSequenceEqual(
                Tenant.objects.annotate(
                    filtered_tokens=FilteredRelation(
                        "tokens",
                        condition=Q(tokens__pk__gte=OuterRef("tokens")),
                    )
                ).filter(filtered_tokens=(1, 1)),
                [self.tenant_1],
            )