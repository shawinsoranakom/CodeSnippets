def test_proxy_to_mti_with_fk_to_proxy_proxy(self):
        # First, test the pk table and field name.
        to_state = self.make_project_state(
            [
                self.author_empty,
                self.author_proxy,
                self.author_proxy_proxy,
                self.book_proxy_proxy_fk,
            ]
        )
        changes = self.get_changes([], to_state)
        fk_field = changes["otherapp"][0].operations[0].fields[1][1]
        self.assertEqual(
            to_state.get_concrete_model_key(fk_field.remote_field.model),
            ("testapp", "author"),
        )
        self.assertEqual(fk_field.remote_field.model, "testapp.AAuthorProxyProxy")

        # Change AuthorProxy to use MTI. FK still points to AAuthorProxyProxy,
        # a proxy of AuthorProxy.
        from_state = to_state.clone()
        to_state = self.make_project_state(
            [
                self.author_empty,
                self.author_proxy_notproxy,
                self.author_proxy_proxy,
                self.book_proxy_proxy_fk,
            ]
        )
        changes = self.get_changes(from_state, to_state)
        # Right number/type of migrations for the AuthorProxy model?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["DeleteModel", "CreateModel"])
        # Right number/type of migrations for the Book model with a FK to
        # AAuthorProxyProxy?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AlterField"])
        # otherapp should depend on testapp.
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("testapp", "auto_1")]
        )
        # Now, test the pk table and field name.
        fk_field = changes["otherapp"][0].operations[0].field
        self.assertEqual(
            to_state.get_concrete_model_key(fk_field.remote_field.model),
            ("testapp", "authorproxy"),
        )
        self.assertEqual(fk_field.remote_field.model, "testapp.AAuthorProxyProxy")