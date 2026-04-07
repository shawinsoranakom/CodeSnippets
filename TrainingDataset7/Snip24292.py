def test_non_concrete_field(self):
        NonConcreteModel.objects.create(point=Point(0, 0), name="name")
        list(NonConcreteModel.objects.all())