def test_create(self):
        """
        Tests making a ProjectState from an Apps
        """

        new_apps = Apps(["migrations"])

        class Author(models.Model):
            name = models.CharField(max_length=255)
            bio = models.TextField()
            age = models.IntegerField(blank=True, null=True)

            class Meta:
                app_label = "migrations"
                apps = new_apps
                unique_together = ["name", "bio"]

        class AuthorProxy(Author):
            class Meta:
                app_label = "migrations"
                apps = new_apps
                proxy = True
                ordering = ["name"]

        class SubAuthor(Author):
            width = models.FloatField(null=True)

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Book(models.Model):
            title = models.CharField(max_length=1000)
            author = models.ForeignKey(Author, models.CASCADE)
            contributors = models.ManyToManyField(Author)

            class Meta:
                app_label = "migrations"
                apps = new_apps
                verbose_name = "tome"
                db_table = "test_tome"
                indexes = [models.Index(fields=["title"])]

        class Food(models.Model):
            food_mgr = FoodManager("a", "b")
            food_qs = FoodQuerySet.as_manager()
            food_no_mgr = NoMigrationFoodManager("x", "y")

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class FoodNoManagers(models.Model):
            class Meta:
                app_label = "migrations"
                apps = new_apps

        class FoodNoDefaultManager(models.Model):
            food_no_mgr = NoMigrationFoodManager("x", "y")
            food_mgr = FoodManager("a", "b")
            food_qs = FoodQuerySet.as_manager()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        mgr1 = FoodManager("a", "b")
        mgr2 = FoodManager("x", "y", c=3, d=4)

        class FoodOrderedManagers(models.Model):
            # The managers on this model should be ordered by their creation
            # counter and not by the order in model body

            food_no_mgr = NoMigrationFoodManager("x", "y")
            food_mgr2 = mgr2
            food_mgr1 = mgr1

            class Meta:
                app_label = "migrations"
                apps = new_apps

        project_state = ProjectState.from_apps(new_apps)
        author_state = project_state.models["migrations", "author"]
        author_proxy_state = project_state.models["migrations", "authorproxy"]
        sub_author_state = project_state.models["migrations", "subauthor"]
        book_state = project_state.models["migrations", "book"]
        food_state = project_state.models["migrations", "food"]
        food_no_managers_state = project_state.models["migrations", "foodnomanagers"]
        food_no_default_manager_state = project_state.models[
            "migrations", "foodnodefaultmanager"
        ]
        food_order_manager_state = project_state.models[
            "migrations", "foodorderedmanagers"
        ]
        book_index = models.Index(fields=["title"])
        book_index.set_name_with_model(Book)

        self.assertEqual(author_state.app_label, "migrations")
        self.assertEqual(author_state.name, "Author")
        self.assertEqual(list(author_state.fields), ["id", "name", "bio", "age"])
        self.assertEqual(author_state.fields["name"].max_length, 255)
        self.assertIs(author_state.fields["bio"].null, False)
        self.assertIs(author_state.fields["age"].null, True)
        self.assertEqual(
            author_state.options,
            {
                "unique_together": {("name", "bio")},
                "indexes": [],
                "constraints": [],
            },
        )
        self.assertEqual(author_state.bases, (models.Model,))

        self.assertEqual(book_state.app_label, "migrations")
        self.assertEqual(book_state.name, "Book")
        self.assertEqual(
            list(book_state.fields), ["id", "title", "author", "contributors"]
        )
        self.assertEqual(book_state.fields["title"].max_length, 1000)
        self.assertIs(book_state.fields["author"].null, False)
        self.assertEqual(
            book_state.fields["contributors"].__class__.__name__, "ManyToManyField"
        )
        self.assertEqual(
            book_state.options,
            {
                "verbose_name": "tome",
                "db_table": "test_tome",
                "indexes": [book_index],
                "constraints": [],
            },
        )
        self.assertEqual(book_state.bases, (models.Model,))

        self.assertEqual(author_proxy_state.app_label, "migrations")
        self.assertEqual(author_proxy_state.name, "AuthorProxy")
        self.assertEqual(author_proxy_state.fields, {})
        self.assertEqual(
            author_proxy_state.options,
            {"proxy": True, "ordering": ["name"], "indexes": [], "constraints": []},
        )
        self.assertEqual(author_proxy_state.bases, ("migrations.author",))

        self.assertEqual(sub_author_state.app_label, "migrations")
        self.assertEqual(sub_author_state.name, "SubAuthor")
        self.assertEqual(len(sub_author_state.fields), 2)
        self.assertEqual(sub_author_state.bases, ("migrations.author",))

        # The default manager is used in migrations
        self.assertEqual([name for name, mgr in food_state.managers], ["food_mgr"])
        self.assertTrue(all(isinstance(name, str) for name, mgr in food_state.managers))
        self.assertEqual(food_state.managers[0][1].args, ("a", "b", 1, 2))

        # No explicit managers defined. Migrations will fall back to the
        # default
        self.assertEqual(food_no_managers_state.managers, [])

        # food_mgr is used in migration but isn't the default mgr, hence add
        # the default
        self.assertEqual(
            [name for name, mgr in food_no_default_manager_state.managers],
            ["food_no_mgr", "food_mgr"],
        )
        self.assertTrue(
            all(
                isinstance(name, str)
                for name, mgr in food_no_default_manager_state.managers
            )
        )
        self.assertEqual(
            food_no_default_manager_state.managers[0][1].__class__, models.Manager
        )
        self.assertIsInstance(food_no_default_manager_state.managers[1][1], FoodManager)

        self.assertEqual(
            [name for name, mgr in food_order_manager_state.managers],
            ["food_mgr1", "food_mgr2"],
        )
        self.assertTrue(
            all(
                isinstance(name, str) for name, mgr in food_order_manager_state.managers
            )
        )
        self.assertEqual(
            [mgr.args for name, mgr in food_order_manager_state.managers],
            [("a", "b", 1, 2), ("x", "y", 3, 4)],
        )