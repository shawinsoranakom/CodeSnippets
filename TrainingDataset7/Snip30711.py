def test_explicit_ordering(self):
        self.assertIs(Annotation.objects.order_by("id").ordered, True)