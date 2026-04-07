def test_empty_queryset(self):
        self.assertIs(Annotation.objects.none().ordered, True)