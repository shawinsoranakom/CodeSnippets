async def assertExportedJsonLines(self, items, rows, settings=None):
        settings = settings or {}
        settings.update(
            {
                "FEEDS": {
                    self._random_temp_filename() / "jl" / self._file_mark: {
                        "format": "jl"
                    },
                },
            }
        )
        batch_size = Settings(settings).getint("FEED_EXPORT_BATCH_ITEM_COUNT")
        rows = [{k: v for k, v in row.items() if v} for row in rows]
        data = await self.exported_data(items, settings)
        for batch in data["jl"]:
            got_batch = [
                json.loads(to_unicode(batch_item)) for batch_item in batch.splitlines()
            ]
            expected_batch, rows = rows[:batch_size], rows[batch_size:]
            assert got_batch == expected_batch