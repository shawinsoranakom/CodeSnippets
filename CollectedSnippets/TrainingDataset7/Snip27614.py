def test_sanity_index_name(self):
        field = models.IntegerField()
        options = {"indexes": [models.Index(fields=["field"])]}
        msg = (
            "Indexes passed to ModelState require a name attribute. <Index: "
            "fields=['field']> doesn't have one."
        )
        with self.assertRaisesMessage(ValueError, msg):
            ModelState("app", "Model", [("field", field)], options=options)