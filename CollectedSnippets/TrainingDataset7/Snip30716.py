def test_annotated_values_default_ordering(self):
        qs = Tag.objects.values("name").annotate(num_notes=Count("pk"))
        self.assertIs(qs.ordered, False)
        self.assertIs(qs.order_by("name").ordered, True)