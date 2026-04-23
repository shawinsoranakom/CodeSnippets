def test_abstract_model_children_inherit_indexes(self):
        class Abstract(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "migrations"
                abstract = True
                indexes = [models.Index(fields=["name"])]

        class Child1(Abstract):
            pass

        class Child2(Abstract):
            pass

        abstract_state = ModelState.from_model(Abstract)
        child1_state = ModelState.from_model(Child1)
        child2_state = ModelState.from_model(Child2)
        index_names = [index.name for index in abstract_state.options["indexes"]]
        self.assertEqual(index_names, ["migrations__name_ae16a4_idx"])
        index_names = [index.name for index in child1_state.options["indexes"]]
        self.assertEqual(index_names, ["migrations__name_b0afd7_idx"])
        index_names = [index.name for index in child2_state.options["indexes"]]
        self.assertEqual(index_names, ["migrations__name_016466_idx"])

        # Modifying the state doesn't modify the index on the model.
        child1_state.options["indexes"][0].name = "bar"
        self.assertEqual(Child1._meta.indexes[0].name, "migrations__name_b0afd7_idx")