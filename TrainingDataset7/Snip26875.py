def test_alter_constraint(self):
        book_constraint = models.CheckConstraint(
            condition=models.Q(title__contains="title"),
            name="title_contains_title",
        )
        book_altered_constraint = models.CheckConstraint(
            condition=models.Q(title__contains="title"),
            name="title_contains_title",
            violation_error_code="error_code",
        )
        author_altered_constraint = models.CheckConstraint(
            condition=models.Q(name__contains="Bob"),
            name="name_contains_bob",
            violation_error_message="Name doesn't contain Bob",
        )

        book_check_constraint = copy.deepcopy(self.book)
        book_check_constraint_with_error_message = copy.deepcopy(self.book)
        author_name_check_constraint_with_error_message = copy.deepcopy(
            self.author_name_check_constraint
        )

        book_check_constraint.options = {"constraints": [book_constraint]}
        book_check_constraint_with_error_message.options = {
            "constraints": [book_altered_constraint]
        }
        author_name_check_constraint_with_error_message.options = {
            "constraints": [author_altered_constraint]
        }

        changes = self.get_changes(
            [self.author_name_check_constraint, book_check_constraint],
            [
                author_name_check_constraint_with_error_message,
                book_check_constraint_with_error_message,
            ],
        )

        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterConstraint"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            model_name="author",
            name="name_contains_bob",
            constraint=author_altered_constraint,
        )

        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AlterConstraint"])
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            0,
            model_name="book",
            name="title_contains_title",
            constraint=book_altered_constraint,
        )
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("testapp", "auto_1")]
        )