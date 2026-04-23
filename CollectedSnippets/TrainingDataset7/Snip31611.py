def test_reverse_related_validation_with_filtered_relation(self):
        fields = "userprofile, userstat, relation"
        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("foobar", fields)
        ):
            list(
                User.objects.annotate(
                    relation=FilteredRelation("userprofile")
                ).select_related("foobar")
            )