def test_proxy(self):
        """The autodetector correctly deals with proxy models."""
        # First, we test adding a proxy model
        changes = self.get_changes(
            [self.author_empty], [self.author_empty, self.author_proxy]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="AuthorProxy",
            options={"proxy": True, "indexes": [], "constraints": []},
        )
        # Now, we test turning a proxy model into a non-proxy model
        # It should delete the proxy then make the real one
        changes = self.get_changes(
            [self.author_empty, self.author_proxy],
            [self.author_empty, self.author_proxy_notproxy],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["DeleteModel", "CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="AuthorProxy")
        self.assertOperationAttributes(
            changes, "testapp", 0, 1, name="AuthorProxy", options={}
        )