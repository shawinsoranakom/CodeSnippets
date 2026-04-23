def test_creates_tag_rows_before_reference_tags(self, db_engine_fk, temp_dir: Path):
        """With PRAGMA foreign_keys=ON, tags must exist in the tags table
        before they can be referenced in asset_reference_tags."""

        @contextmanager
        def _create_session():
            with SASession(db_engine_fk) as sess:
                yield sess

        file_path = temp_dir / "output.png"
        file_path.write_bytes(b"image data")

        with patch("app.assets.services.ingest.create_session", _create_session), \
             patch(
                 "app.assets.services.ingest.get_name_and_tags_from_asset_path",
                 return_value=("output.png", ["output"]),
             ):
            result = ingest_existing_file(
                abs_path=str(file_path),
                extra_tags=["my-job"],
            )

        assert result is True

        with SASession(db_engine_fk) as sess:
            tag_names = {t.name for t in sess.query(Tag).all()}
            assert "output" in tag_names
            assert "my-job" in tag_names

            ref_tags = sess.query(AssetReferenceTag).all()
            ref_tag_names = {rt.tag_name for rt in ref_tags}
            assert "output" in ref_tag_names
            assert "my-job" in ref_tag_names