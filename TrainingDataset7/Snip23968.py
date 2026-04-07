def test_dwithin_subquery(self):
        """dwithin lookup in a subquery using OuterRef as a parameter."""
        qs = CensusZipcode.objects.annotate(
            annotated_value=Exists(
                SouthTexasCity.objects.filter(
                    point__dwithin=(OuterRef("poly"), D(m=10)),
                )
            )
        ).filter(annotated_value=True)
        self.assertEqual(self.get_names(qs), ["77002", "77025", "77401"])