def test_basic(self):
        querysets = [
            Tag.objects.filter(name="test"),
            Tag.objects.filter(name="test").select_related("parent"),
            Tag.objects.filter(name="test").prefetch_related("children"),
            Tag.objects.filter(name="test").annotate(Count("children")),
            Tag.objects.filter(name="test").values_list("name"),
        ]
        if connection.features.supports_select_union:
            querysets.append(
                Tag.objects.order_by().union(Tag.objects.order_by().filter(name="test"))
            )
        if connection.features.has_select_for_update:
            querysets.append(Tag.objects.select_for_update().filter(name="test"))
        supported_formats = connection.features.supported_explain_formats
        all_formats = (
            (None,)
            + tuple(supported_formats)
            + tuple(f.lower() for f in supported_formats)
        )
        for idx, queryset in enumerate(querysets):
            for format in all_formats:
                with self.subTest(format=format, queryset=idx):
                    with self.assertNumQueries(1) as captured_queries:
                        result = queryset.explain(format=format)
                        self.assertTrue(
                            captured_queries[0]["sql"].startswith(
                                connection.ops.explain_prefix
                            )
                        )
                        self.assertIsInstance(result, str)
                        self.assertTrue(result)
                        if not format:
                            continue
                        if format.lower() == "xml":
                            try:
                                xml.etree.ElementTree.fromstring(result)
                            except xml.etree.ElementTree.ParseError as e:
                                self.fail(
                                    f"QuerySet.explain() result is not valid XML: {e}"
                                )
                        elif format.lower() == "json":
                            try:
                                json.loads(result)
                            except json.JSONDecodeError as e:
                                self.fail(
                                    f"QuerySet.explain() result is not valid JSON: {e}"
                                )