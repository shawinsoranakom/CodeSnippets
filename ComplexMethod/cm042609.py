def test_same_name_as_existing_file(self, force: bool, tmp_path: Path) -> None:
        file_name = "example"
        file_path = Path(tmp_path, file_name + ".py")
        _, out, _ = proc("genspider", file_name, "example.com", cwd=tmp_path)
        assert f"Created spider {file_name!r} using template 'basic' " in out
        assert file_path.exists()
        modify_time_before = file_path.stat().st_mtime
        file_contents_before = file_path.read_text(encoding="utf-8")

        if force:
            # use different template to ensure contents were changed
            _, out, _ = proc(
                "genspider",
                "--force",
                "-t",
                "crawl",
                file_name,
                "example.com",
                cwd=tmp_path,
            )
            assert f"Created spider {file_name!r} using template 'crawl' " in out
            modify_time_after = file_path.stat().st_mtime
            assert modify_time_after != modify_time_before
            file_contents_after = file_path.read_text(encoding="utf-8")
            assert file_contents_after != file_contents_before
        else:
            _, out, _ = proc("genspider", file_name, "example.com", cwd=tmp_path)
            assert (
                f"{Path(tmp_path, file_name + '.py').resolve()} already exists" in out
            )
            modify_time_after = file_path.stat().st_mtime
            assert modify_time_after == modify_time_before
            file_contents_after = file_path.read_text(encoding="utf-8")
            assert file_contents_after == file_contents_before