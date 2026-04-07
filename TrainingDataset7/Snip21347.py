def test_slicing_of_outerref(self):
        inner = Company.objects.filter(name__startswith=OuterRef("ceo__firstname")[0])
        outer = Company.objects.filter(Exists(inner)).values_list("name", flat=True)
        self.assertSequenceEqual(outer, ["Foobar Ltd."])