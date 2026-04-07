def test_select_related_works_on_parent_model_fields(self):
        # select_related works with fields from the parent object as if they
        # were a normal part of the model.
        self.assertNumQueries(2, lambda: ItalianRestaurant.objects.all()[0].chef)
        self.assertNumQueries(
            1, lambda: ItalianRestaurant.objects.select_related("chef")[0].chef
        )