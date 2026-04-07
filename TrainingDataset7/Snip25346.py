def test_diamond_mti_common_parent(self):
        class GrandParent(models.Model):
            pass

        class Parent(GrandParent):
            pass

        class Child(Parent):
            pass

        class MTICommonParentModel(Child, GrandParent):
            pass

        self.assertEqual(
            MTICommonParentModel.check(),
            [
                Error(
                    "The field 'grandparent_ptr' clashes with the field "
                    "'grandparent_ptr' from model 'invalid_models_tests.parent'.",
                    obj=MTICommonParentModel,
                    id="models.E006",
                )
            ],
        )