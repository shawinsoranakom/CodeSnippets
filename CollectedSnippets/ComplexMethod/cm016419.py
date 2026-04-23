def test_marks_references_missing_outside_prefixes(self, session: Session, tmp_path):
        asset = _make_asset(session, "hash1")
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        valid_path = str(valid_dir / "file.bin")
        invalid_path = str(invalid_dir / "file.bin")

        _make_reference(session, asset, valid_path, name="valid")
        _make_reference(session, asset, invalid_path, name="invalid")
        session.commit()

        marked = mark_references_missing_outside_prefixes(session, [str(valid_dir)])
        session.commit()

        assert marked == 1
        all_refs = session.query(AssetReference).all()
        assert len(all_refs) == 2

        valid_ref = next(r for r in all_refs if r.file_path == valid_path)
        invalid_ref = next(r for r in all_refs if r.file_path == invalid_path)
        assert valid_ref.is_missing is False
        assert invalid_ref.is_missing is True