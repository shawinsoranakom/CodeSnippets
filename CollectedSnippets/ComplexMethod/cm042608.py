def test_same_filename_as_existing_spider(
        self, force: bool, proj_path: Path
    ) -> None:
        file_name = "example"
        file_path = proj_path / self.project_name / "spiders" / f"{file_name}.py"
        assert call("genspider", file_name, "example.com", cwd=proj_path) == 0
        assert file_path.exists()

        # change name of spider but not its file name
        with file_path.open("r+", encoding="utf-8") as spider_file:
            file_data = spider_file.read()
            file_data = file_data.replace('name = "example"', 'name = "renamed"')
            spider_file.seek(0)
            spider_file.write(file_data)
            spider_file.truncate()
        modify_time_before = file_path.stat().st_mtime
        file_contents_before = file_data

        if force:
            _, out, _ = proc(
                "genspider", "--force", file_name, "example.com", cwd=proj_path
            )
            assert (
                f"Created spider {file_name!r} using template 'basic' in module" in out
            )
            modify_time_after = file_path.stat().st_mtime
            assert modify_time_after != modify_time_before
            file_contents_after = file_path.read_text(encoding="utf-8")
            assert file_contents_after != file_contents_before
        else:
            _, out, _ = proc("genspider", file_name, "example.com", cwd=proj_path)
            assert f"{file_path.resolve()} already exists" in out
            modify_time_after = file_path.stat().st_mtime
            assert modify_time_after == modify_time_before
            file_contents_after = file_path.read_text(encoding="utf-8")
            assert file_contents_after == file_contents_before