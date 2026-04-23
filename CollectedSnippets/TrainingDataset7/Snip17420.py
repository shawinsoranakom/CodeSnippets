async def test_aexplain(self):
        supported_formats = await sync_to_async(self._get_db_feature)(
            connection, "supported_explain_formats"
        )
        all_formats = (None, *supported_formats)
        for format_ in all_formats:
            with self.subTest(format=format_):
                # TODO: Check the captured query when async versions of
                # self.assertNumQueries/CaptureQueriesContext context
                # processors are available.
                result = await SimpleModel.objects.filter(field=1).aexplain(
                    format=format_
                )
                self.assertIsInstance(result, str)
                self.assertTrue(result)
                if not format_:
                    continue
                if format_.lower() == "xml":
                    try:
                        xml.etree.ElementTree.fromstring(result)
                    except xml.etree.ElementTree.ParseError as e:
                        self.fail(f"QuerySet.aexplain() result is not valid XML: {e}")
                elif format_.lower() == "json":
                    try:
                        json.loads(result)
                    except json.JSONDecodeError as e:
                        self.fail(f"QuerySet.aexplain() result is not valid JSON: {e}")