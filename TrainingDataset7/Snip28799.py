def test_first_relation_tree_access_populates_all(self):
        # On first access, relation tree should have populated cache.
        self.assertTrue(self.all_models[0]._meta._relation_tree)

        # AbstractPerson does not have any relations, so relation_tree
        # should just return an EMPTY_RELATION_TREE.
        self.assertEqual(AbstractPerson._meta._relation_tree, EMPTY_RELATION_TREE)

        # All the other models should already have their relation tree
        # in the internal __dict__ .
        all_models_but_abstractperson = (
            m for m in self.all_models if m is not AbstractPerson
        )
        for m in all_models_but_abstractperson:
            self.assertIn("_relation_tree", m._meta.__dict__)