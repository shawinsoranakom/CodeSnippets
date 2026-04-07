def test_unique_and_reverse_m2m(self):
        """
        AlterField can modify a unique field when there's a reverse M2M
        relation on the model.
        """

        class Tag(Model):
            title = CharField(max_length=255)
            slug = SlugField(unique=True)

            class Meta:
                app_label = "schema"

        class Book(Model):
            tags = ManyToManyField(Tag, related_name="books")

            class Meta:
                app_label = "schema"

        self.isolated_local_models = [Book._meta.get_field("tags").remote_field.through]
        with connection.schema_editor() as editor:
            editor.create_model(Tag)
            editor.create_model(Book)
        new_field = SlugField(max_length=75, unique=True)
        new_field.model = Tag
        new_field.set_attributes_from_name("slug")
        with self.assertLogs("django.db.backends.schema", "DEBUG") as cm:
            with connection.schema_editor() as editor:
                editor.alter_field(Tag, Tag._meta.get_field("slug"), new_field)
        # One SQL statement is executed to alter the field.
        self.assertEqual(len(cm.records), 1)
        # Ensure that the field is still unique.
        Tag.objects.create(title="foo", slug="foo")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(title="bar", slug="foo")