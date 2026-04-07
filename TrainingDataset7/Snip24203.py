def test_isempty_geometry_null(self):
        nowhere = State.objects.create(name="Nowhere", poly=None)
        qs = State.objects.annotate(isempty=functions.IsEmpty("poly"))
        self.assertSequenceEqual(qs.filter(isempty=None), [nowhere])
        self.assertSequenceEqual(
            qs.filter(isempty=False).order_by("name").values_list("name", flat=True),
            ["Colorado", "Kansas"],
        )
        self.assertSequenceEqual(qs.filter(isempty=True), [])
        self.assertSequenceEqual(State.objects.filter(poly__isempty=True), [])