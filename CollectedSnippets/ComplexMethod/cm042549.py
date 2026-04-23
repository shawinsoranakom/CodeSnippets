async def assertExportedMultiple(
        self,
        items: Iterable[Any],
        rows: Iterable[dict[str, Any]],
        settings: dict[str, Any] | None = None,
    ) -> None:
        settings = settings or {}
        settings.update(
            {
                "FEEDS": {
                    self._random_temp_filename(): {"format": "xml"},
                    self._random_temp_filename(): {"format": "json"},
                },
            }
        )
        data = await self.exported_data(items, settings)
        rows = [{k: v for k, v in row.items() if v} for row in rows]
        # XML
        root = lxml.etree.fromstring(data["xml"])
        xml_rows = [{e.tag: e.text for e in it} for it in root.findall("item")]
        assert rows == xml_rows
        # JSON
        json_rows = json.loads(to_unicode(data["json"]))
        assert rows == json_rows