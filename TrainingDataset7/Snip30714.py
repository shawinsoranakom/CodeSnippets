def test_annotated_ordering(self):
        qs = Annotation.objects.annotate(num_notes=Count("notes"))
        self.assertIs(qs.ordered, False)
        self.assertIs(qs.order_by("num_notes").ordered, True)