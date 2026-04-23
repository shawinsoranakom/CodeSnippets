def test_opclasses_requires_index_name(self):
        with self.assertRaisesMessage(
            ValueError, "An index must be named to use opclasses."
        ):
            models.Index(opclasses=["jsonb_path_ops"])