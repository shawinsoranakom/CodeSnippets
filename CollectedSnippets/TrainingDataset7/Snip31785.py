def test_serialize_only_pk(self):
        with self.assertNumQueries(7) as ctx:
            serializers.serialize(
                self.serializer_name,
                Article.objects.all(),
                use_natural_foreign_keys=False,
            )

        categories_sql = ctx[1]["sql"]
        self.assertNotIn(connection.ops.quote_name("meta_data_id"), categories_sql)
        meta_data_sql = ctx[2]["sql"]
        self.assertNotIn(connection.ops.quote_name("kind"), meta_data_sql)
        topics_data_sql = ctx[3]["sql"]
        self.assertNotIn(connection.ops.quote_name("category_id"), topics_data_sql)