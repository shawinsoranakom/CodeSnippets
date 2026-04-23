def test_boundary_conditions(self):
        # Boundary conditions on a PositiveIntegerField.
        class BoundaryForm(ModelForm):
            class Meta:
                model = BoundaryModel
                fields = "__all__"

        f = BoundaryForm({"positive_integer": 100})
        self.assertTrue(f.is_valid())
        f = BoundaryForm({"positive_integer": 0})
        self.assertTrue(f.is_valid())
        f = BoundaryForm({"positive_integer": -100})
        self.assertFalse(f.is_valid())