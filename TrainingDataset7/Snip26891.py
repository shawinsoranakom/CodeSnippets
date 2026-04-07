def test_proxy_non_model_parent(self):
        class Mixin:
            pass

        author_proxy_non_model_parent = ModelState(
            "testapp",
            "AuthorProxy",
            [],
            {"proxy": True},
            (Mixin, "testapp.author"),
        )
        changes = self.get_changes(
            [self.author_empty],
            [self.author_empty, author_proxy_non_model_parent],
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="AuthorProxy",
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=(Mixin, "testapp.author"),
        )