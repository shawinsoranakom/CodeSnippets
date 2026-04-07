def _test_autofield_foreignfield_growth(
        self, source_field, target_field, target_value
    ):
        """
        A field may be migrated in the following ways:

        - AutoField to BigAutoField
        - SmallAutoField to AutoField
        - SmallAutoField to BigAutoField
        """

        def create_initial_data(models, schema_editor):
            Article = models.get_model("test_article", "Article")
            Blog = models.get_model("test_blog", "Blog")
            blog = Blog.objects.create(name="web development done right")
            Article.objects.create(name="Frameworks", blog=blog)
            Article.objects.create(name="Programming Languages", blog=blog)

        def create_big_data(models, schema_editor):
            Article = models.get_model("test_article", "Article")
            Blog = models.get_model("test_blog", "Blog")
            blog2 = Blog.objects.create(name="Frameworks", id=target_value)
            Article.objects.create(name="Django", blog=blog2)
            Article.objects.create(id=target_value, name="Django2", blog=blog2)

        create_blog = migrations.CreateModel(
            "Blog",
            [
                ("id", source_field(primary_key=True)),
                ("name", models.CharField(max_length=100)),
            ],
            options={},
        )
        create_article = migrations.CreateModel(
            "Article",
            [
                ("id", source_field(primary_key=True)),
                (
                    "blog",
                    models.ForeignKey(to="test_blog.Blog", on_delete=models.CASCADE),
                ),
                ("name", models.CharField(max_length=100)),
                ("data", models.TextField(default="")),
            ],
            options={},
        )
        fill_initial_data = migrations.RunPython(
            create_initial_data, create_initial_data
        )
        fill_big_data = migrations.RunPython(create_big_data, create_big_data)

        grow_article_id = migrations.AlterField(
            "Article", "id", target_field(primary_key=True)
        )
        grow_blog_id = migrations.AlterField(
            "Blog", "id", target_field(primary_key=True)
        )

        project_state = ProjectState()
        new_state = project_state.clone()
        with connection.schema_editor() as editor:
            create_blog.state_forwards("test_blog", new_state)
            create_blog.database_forwards("test_blog", editor, project_state, new_state)

        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            create_article.state_forwards("test_article", new_state)
            create_article.database_forwards(
                "test_article", editor, project_state, new_state
            )

        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            fill_initial_data.state_forwards("fill_initial_data", new_state)
            fill_initial_data.database_forwards(
                "fill_initial_data", editor, project_state, new_state
            )

        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            grow_article_id.state_forwards("test_article", new_state)
            grow_article_id.database_forwards(
                "test_article", editor, project_state, new_state
            )

        state = new_state.clone()
        article = state.apps.get_model("test_article.Article")
        self.assertIsInstance(article._meta.pk, target_field)

        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            grow_blog_id.state_forwards("test_blog", new_state)
            grow_blog_id.database_forwards(
                "test_blog", editor, project_state, new_state
            )

        state = new_state.clone()
        blog = state.apps.get_model("test_blog.Blog")
        self.assertIsInstance(blog._meta.pk, target_field)

        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            fill_big_data.state_forwards("fill_big_data", new_state)
            fill_big_data.database_forwards(
                "fill_big_data", editor, project_state, new_state
            )