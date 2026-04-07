def test_namespaced_db_table(self):
        if not connection.ops.postgis:
            self.skipTest("PostGIS-specific test.")

        class SchemaCity(models.Model):
            point = models.PointField()

            class Meta:
                app_label = "geoapp"
                db_table = 'django_schema"."geoapp_schema_city'

        index = Index(fields=["point"])
        editor = connection.schema_editor()
        create_index_sql = str(index.create_sql(SchemaCity, editor))
        self.assertIn(
            "%s USING " % editor.quote_name(SchemaCity._meta.db_table),
            create_index_sql,
        )
        self.assertIn(
            'CREATE INDEX "geoapp_schema_city_point_9ed70651_id" ',
            create_index_sql,
        )