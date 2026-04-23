def test_metadata_preserved_with_full_origin(self, monkeypatch):
        fake_doc = _FakeDoclingDocument(
            name="report.pdf",
            origin=_FakeOrigin(
                filename="report.pdf",
                binary_hash="abc123hash",
                mimetype="application/pdf",
            ),
            markdown_text="# Report",
        )

        results = self._run_export(monkeypatch, fake_doc)

        assert len(results) == 1
        data = results[0]
        assert data.get_text() == "# Report"
        assert data.data["export_format"] == "Markdown"
        assert data.data["name"] == "report.pdf"
        assert data.data["filename"] == "report.pdf"
        assert data.data["document_id"] == "abc123hash"
        assert data.data["mimetype"] == "application/pdf"