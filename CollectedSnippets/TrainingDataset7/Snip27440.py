def test_run_python_related_assignment(self):
        """
        #24282 - Model changes to a FK reverse side update the model
        on the FK side as well.
        """

        def inner_method(models, schema_editor):
            Author = models.get_model("test_authors", "Author")
            Book = models.get_model("test_books", "Book")
            author = Author.objects.create(name="Hemingway")
            Book.objects.create(title="Old Man and The Sea", author=author)

        create_author = migrations.CreateModel(
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=100)),
            ],
            options={},
        )
        create_book = migrations.CreateModel(
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("title", models.CharField(max_length=100)),
                ("author", models.ForeignKey("test_authors.Author", models.CASCADE)),
            ],
            options={},
        )
        add_hometown = migrations.AddField(
            "Author",
            "hometown",
            models.CharField(max_length=100),
        )
        create_old_man = migrations.RunPython(inner_method, inner_method)

        project_state = ProjectState()
        new_state = project_state.clone()
        with connection.schema_editor() as editor:
            create_author.state_forwards("test_authors", new_state)
            create_author.database_forwards(
                "test_authors", editor, project_state, new_state
            )
        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            create_book.state_forwards("test_books", new_state)
            create_book.database_forwards(
                "test_books", editor, project_state, new_state
            )
        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            add_hometown.state_forwards("test_authors", new_state)
            add_hometown.database_forwards(
                "test_authors", editor, project_state, new_state
            )
        project_state = new_state
        new_state = new_state.clone()
        with connection.schema_editor() as editor:
            create_old_man.state_forwards("test_books", new_state)
            create_old_man.database_forwards(
                "test_books", editor, project_state, new_state
            )