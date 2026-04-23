def test_custom_manager_swappable(self):
        """
        Tests making a ProjectState from unused models with custom managers
        """
        new_apps = Apps(["migrations"])

        class Food(models.Model):
            food_mgr = FoodManager("a", "b")
            food_qs = FoodQuerySet.as_manager()
            food_no_mgr = NoMigrationFoodManager("x", "y")

            class Meta:
                app_label = "migrations"
                apps = new_apps
                swappable = "TEST_SWAPPABLE_MODEL"

        food_state = ModelState.from_model(Food)

        # The default manager is used in migrations
        self.assertEqual([name for name, mgr in food_state.managers], ["food_mgr"])
        self.assertEqual(food_state.managers[0][1].args, ("a", "b", 1, 2))