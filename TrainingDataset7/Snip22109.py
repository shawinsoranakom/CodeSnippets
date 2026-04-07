def test_with_empty_relation_name_error(self):
        with self.assertRaisesMessage(ValueError, "relation_name cannot be empty."):
            FilteredRelation("", condition=Q(blank=""))