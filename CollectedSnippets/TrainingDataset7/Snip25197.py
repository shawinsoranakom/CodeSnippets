def test_no_index_for_foreignkey(self):
        """
        MySQL on InnoDB already creates indexes automatically for foreign keys.
        (#14180). An index should be created if db_constraint=False (#26171).
        """
        with connection.cursor() as cursor:
            storage = connection.introspection.get_storage_engine(
                cursor,
                ArticleTranslation._meta.db_table,
            )
        if storage != "InnoDB":
            self.skipTest("This test only applies to the InnoDB storage engine")
        index_sql = [
            str(statement)
            for statement in connection.schema_editor()._model_indexes_sql(
                ArticleTranslation
            )
        ]
        self.assertEqual(
            index_sql,
            [
                "CREATE INDEX "
                "`indexes_articletranslation_article_no_constraint_id_d6c0806b` "
                "ON `indexes_articletranslation` (`article_no_constraint_id`)"
            ],
        )

        # The index also shouldn't be created if the ForeignKey is added after
        # the model was created.
        field_created = False
        try:
            with connection.schema_editor() as editor:
                new_field = ForeignKey(Article, CASCADE)
                new_field.set_attributes_from_name("new_foreign_key")
                editor.add_field(ArticleTranslation, new_field)
                field_created = True
                # No deferred SQL. The FK constraint is included in the
                # statement to add the field.
                self.assertFalse(editor.deferred_sql)
        finally:
            if field_created:
                with connection.schema_editor() as editor:
                    editor.remove_field(ArticleTranslation, new_field)