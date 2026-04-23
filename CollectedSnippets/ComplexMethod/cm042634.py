async def assertExportedMultiple(self, items, rows, settings=None):
        settings = settings or {}
        settings.update(
            {
                "FEEDS": {
                    self._random_temp_filename() / "xml" / self._file_mark: {
                        "format": "xml"
                    },
                    self._random_temp_filename() / "json" / self._file_mark: {
                        "format": "json"
                    },
                },
            }
        )
        batch_size = Settings(settings).getint("FEED_EXPORT_BATCH_ITEM_COUNT")
        rows = [{k: v for k, v in row.items() if v} for row in rows]
        data = await self.exported_data(items, settings)
        # XML
        xml_rows = rows.copy()
        for batch in data["xml"]:
            root = lxml.etree.fromstring(batch)
            got_batch = [{e.tag: e.text for e in it} for it in root.findall("item")]
            expected_batch, xml_rows = xml_rows[:batch_size], xml_rows[batch_size:]
            assert got_batch == expected_batch
        # JSON
        json_rows = rows.copy()
        for batch in data["json"]:
            got_batch = json.loads(batch.decode("utf-8"))
            expected_batch, json_rows = json_rows[:batch_size], json_rows[batch_size:]
            assert got_batch == expected_batch