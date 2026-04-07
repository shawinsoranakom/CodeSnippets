def test_filter_wrong_annotation(self):
        with self.assertRaisesMessage(
            FieldError, "Cannot resolve keyword 'nope' into field."
        ):
            list(
                Book.objects.annotate(sum_rating=Sum("rating")).filter(
                    sum_rating=F("nope")
                )
            )