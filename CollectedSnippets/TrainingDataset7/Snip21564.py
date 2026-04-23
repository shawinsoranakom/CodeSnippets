def test_annotate_with_empty_when(self):
        objects = CaseTestModel.objects.annotate(
            selected=Case(
                When(pk__in=[], then=Value("selected")),
                default=Value("not selected"),
            )
        )
        self.assertEqual(len(objects), CaseTestModel.objects.count())
        self.assertTrue(all(obj.selected == "not selected" for obj in objects))