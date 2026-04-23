def test_annotate_filter_decimal(self):
        obj = CaseTestModel.objects.create(integer=0, decimal=Decimal("1"))
        qs = CaseTestModel.objects.annotate(
            x=Case(When(integer=0, then=F("decimal"))),
            y=Case(When(integer=0, then=Value(Decimal("1")))),
        )
        self.assertSequenceEqual(qs.filter(Q(x=1) & Q(x=Decimal("1"))), [obj])
        self.assertSequenceEqual(qs.filter(Q(y=1) & Q(y=Decimal("1"))), [obj])