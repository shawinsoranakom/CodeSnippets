def test_dangling_references_throw_error(self):
        new_apps = Apps()

        class Author(models.Model):
            name = models.TextField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Publisher(models.Model):
            name = models.TextField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Book(models.Model):
            author = models.ForeignKey(Author, models.CASCADE)
            publisher = models.ForeignKey(Publisher, models.CASCADE)

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Magazine(models.Model):
            authors = models.ManyToManyField(Author)

            class Meta:
                app_label = "migrations"
                apps = new_apps

        # Make a valid ProjectState and render it
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(Author))
        project_state.add_model(ModelState.from_model(Publisher))
        project_state.add_model(ModelState.from_model(Book))
        project_state.add_model(ModelState.from_model(Magazine))
        self.assertEqual(len(project_state.apps.get_models()), 4)

        # now make an invalid one with a ForeignKey
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(Book))
        msg = (
            "The field migrations.Book.author was declared with a lazy reference "
            "to 'migrations.author', but app 'migrations' doesn't provide model "
            "'author'.\n"
            "The field migrations.Book.publisher was declared with a lazy reference "
            "to 'migrations.publisher', but app 'migrations' doesn't provide model "
            "'publisher'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            project_state.apps

        # And another with ManyToManyField.
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(Magazine))
        msg = (
            "The field migrations.Magazine.authors was declared with a lazy reference "
            "to 'migrations.author', but app 'migrations' doesn't provide model "
            "'author'.\n"
            "The field migrations.Magazine_authors.author was declared with a lazy "
            "reference to 'migrations.author', but app 'migrations' doesn't provide "
            "model 'author'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            project_state.apps

        # And now with multiple models and multiple fields.
        project_state.add_model(ModelState.from_model(Book))
        msg = (
            "The field migrations.Book.author was declared with a lazy reference "
            "to 'migrations.author', but app 'migrations' doesn't provide model "
            "'author'.\n"
            "The field migrations.Book.publisher was declared with a lazy reference "
            "to 'migrations.publisher', but app 'migrations' doesn't provide model "
            "'publisher'.\n"
            "The field migrations.Magazine.authors was declared with a lazy reference "
            "to 'migrations.author', but app 'migrations' doesn't provide model "
            "'author'.\n"
            "The field migrations.Magazine_authors.author was declared with a lazy "
            "reference to 'migrations.author', but app 'migrations' doesn't provide "
            "model 'author'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            project_state.apps