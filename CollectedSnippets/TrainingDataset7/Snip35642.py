def test_update_transformed_field(self):
        A.objects.create(x=5)
        A.objects.create(x=-6)
        with register_lookup(IntegerField, Abs):
            A.objects.update(x=F("x__abs"))
            self.assertCountEqual(A.objects.values_list("x", flat=True), [5, 6])