def test_subquery_aliases(self):
        combined = School.objects.filter(pk__isnull=False) & School.objects.filter(
            Exists(
                Classroom.objects.filter(
                    has_blackboard=True,
                    school=OuterRef("pk"),
                )
            ),
        )
        self.assertSequenceEqual(combined, [self.school])
        nested_combined = School.objects.filter(pk__in=combined.values("pk"))
        self.assertSequenceEqual(nested_combined, [self.school])