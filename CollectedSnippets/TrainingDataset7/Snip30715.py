def test_annotated_default_ordering(self):
        qs = Tag.objects.annotate(num_notes=Count("pk"))
        self.assertIs(qs.ordered, False)
        self.assertIs(qs.order_by("name").ordered, True)