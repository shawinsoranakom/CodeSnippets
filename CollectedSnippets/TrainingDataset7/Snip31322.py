def test_alter_null_with_default_value_deferred_constraints(self):
        class Publisher(Model):
            class Meta:
                app_label = "schema"

        class Article(Model):
            publisher = ForeignKey(Publisher, CASCADE)
            title = CharField(max_length=50, null=True)
            description = CharField(max_length=100, null=True)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Publisher)
            editor.create_model(Article)
        self.isolated_local_models = [Article, Publisher]

        publisher = Publisher.objects.create()
        Article.objects.create(publisher=publisher)

        old_title = Article._meta.get_field("title")
        new_title = CharField(max_length=50, null=False, default="")
        new_title.set_attributes_from_name("title")
        old_description = Article._meta.get_field("description")
        new_description = CharField(max_length=100, null=False, default="")
        new_description.set_attributes_from_name("description")
        with connection.schema_editor() as editor:
            editor.alter_field(Article, old_title, new_title, strict=True)
            editor.alter_field(Article, old_description, new_description, strict=True)