def test_col_alias_quoted(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertEqual(
                Tag.objects.values("parent")
                .annotate(
                    tag_per_parent=Count("pk"),
                )
                .aggregate(Max("tag_per_parent")),
                {"tag_per_parent__max": 2},
            )
        sql = captured_queries[0]["sql"]
        self.assertIn("AS %s" % connection.ops.quote_name("parent"), sql)