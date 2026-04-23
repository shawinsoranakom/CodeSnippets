def test_case_reuse(self):
        SOME_CASE = Case(
            When(pk=0, then=Value("0")),
            default=Value("1"),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(somecase=SOME_CASE).order_by("pk"),
            CaseTestModel.objects.annotate(somecase=SOME_CASE)
            .order_by("pk")
            .values_list("pk", "somecase"),
            lambda x: (x.pk, x.somecase),
        )