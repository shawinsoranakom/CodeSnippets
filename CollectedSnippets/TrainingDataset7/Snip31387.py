def _test_m2m_repoint(self, M2MFieldClass):
        """
        Tests repointing M2M fields
        """

        class LocalBookWithM2M(Model):
            author = ForeignKey(Author, CASCADE)
            title = CharField(max_length=100, db_index=True)
            pub_date = DateTimeField()
            tags = M2MFieldClass("TagM2MTest", related_name="books")

            class Meta:
                app_label = "schema"
                apps = new_apps

        self.local_models = [LocalBookWithM2M]
        # Create the tables
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(LocalBookWithM2M)
            editor.create_model(TagM2MTest)
            editor.create_model(UniqueTest)
        # Ensure the M2M exists and points to TagM2MTest
        if connection.features.supports_foreign_keys:
            self.assertForeignKeyExists(
                LocalBookWithM2M._meta.get_field("tags").remote_field.through,
                "tagm2mtest_id",
                "schema_tagm2mtest",
            )
        # Repoint the M2M
        old_field = LocalBookWithM2M._meta.get_field("tags")
        new_field = M2MFieldClass(UniqueTest)
        new_field.contribute_to_class(LocalBookWithM2M, "uniques")
        with connection.schema_editor() as editor:
            editor.alter_field(LocalBookWithM2M, old_field, new_field, strict=True)
        # Ensure old M2M is gone
        with self.assertRaises(DatabaseError):
            self.column_classes(
                LocalBookWithM2M._meta.get_field("tags").remote_field.through
            )

        # This model looks like the new model and is used for teardown.
        opts = LocalBookWithM2M._meta
        opts.local_many_to_many.remove(old_field)
        # Ensure the new M2M exists and points to UniqueTest
        if connection.features.supports_foreign_keys:
            self.assertForeignKeyExists(
                new_field.remote_field.through, "uniquetest_id", "schema_uniquetest"
            )