def test_creates_asset_and_reference(self, mock_create_session, temp_dir: Path, session: Session):
        file_path = temp_dir / "test_file.bin"
        file_path.write_bytes(b"test content")

        result = _ingest_file_from_path(
            abs_path=str(file_path),
            asset_hash="blake3:abc123",
            size_bytes=12,
            mtime_ns=1234567890000000000,
            mime_type="application/octet-stream",
        )

        assert result.asset_created is True
        assert result.ref_created is True
        assert result.reference_id is not None

        # Verify DB state
        assets = session.query(Asset).all()
        assert len(assets) == 1
        assert assets[0].hash == "blake3:abc123"

        refs = session.query(AssetReference).all()
        assert len(refs) == 1
        assert refs[0].file_path == str(file_path)