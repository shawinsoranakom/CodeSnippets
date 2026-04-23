def test_proxy_to_mti_with_fk_to_proxy(self):
        # First, test the pk table and field name.
        to_state = self.make_project_state(
            [self.author_empty, self.author_proxy_third, self.book_proxy_fk],
        )
        changes = self.get_changes([], to_state)
        fk_field = changes["otherapp"][0].operations[0].fields[2][1]
        self.assertEqual(
            to_state.get_concrete_model_key(fk_field.remote_field.model),
            ("testapp", "author"),
        )
        self.assertEqual(fk_field.remote_field.model, "thirdapp.AuthorProxy")

        # Change AuthorProxy to use MTI.
        from_state = to_state.clone()
        to_state = self.make_project_state(
            [self.author_empty, self.author_proxy_third_notproxy, self.book_proxy_fk],
        )
        changes = self.get_changes(from_state, to_state)
        # Right number/type of migrations for the AuthorProxy model?
        self.assertNumberMigrations(changes, "thirdapp", 1)
        self.assertOperationTypes(
            changes, "thirdapp", 0, ["DeleteModel", "CreateModel"]
        )
        # Right number/type of migrations for the Book model with a FK to
        # AuthorProxy?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AlterField"])
        # otherapp should depend on thirdapp.
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("thirdapp", "auto_1")]
        )
        # Now, test the pk table and field name.
        fk_field = changes["otherapp"][0].operations[0].field
        self.assertEqual(
            to_state.get_concrete_model_key(fk_field.remote_field.model),
            ("thirdapp", "authorproxy"),
        )
        self.assertEqual(fk_field.remote_field.model, "thirdapp.AuthorProxy")