def test_no_default_or_explicit_ordering(self):
        self.assertIs(Annotation.objects.all().ordered, False)