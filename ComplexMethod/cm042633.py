async def assertExportedXml(self, items, rows, settings=None):
        settings = settings or {}
        settings.update(
            {
                "FEEDS": {
                    self._random_temp_filename() / "xml" / self._file_mark: {
                        "format": "xml"
                    },
                },
            }
        )
        batch_size = Settings(settings).getint("FEED_EXPORT_BATCH_ITEM_COUNT")
        rows = [{k: v for k, v in row.items() if v} for row in rows]
        data = await self.exported_data(items, settings)
        for batch in data["xml"]:
            root = lxml.etree.fromstring(batch)
            got_batch = [{e.tag: e.text for e in it} for it in root.findall("item")]
            expected_batch, rows = rows[:batch_size], rows[batch_size:]
            assert got_batch == expected_batch