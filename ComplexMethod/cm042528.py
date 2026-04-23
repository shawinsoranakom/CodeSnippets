def test_startproject_with_project_dir(self, tmp_path: Path) -> None:
        # with a dir arg creates the project in the specified dir
        project_dir = tmp_path / "project"
        assert (
            call("startproject", self.project_name, str(project_dir), cwd=tmp_path) == 0
        )
        self._assert_files_exist(project_dir, self.project_name)

        assert (
            call(
                "startproject", self.project_name, str(project_dir) + "2", cwd=tmp_path
            )
            == 0
        )

        assert (
            call("startproject", self.project_name, str(project_dir), cwd=tmp_path) == 1
        )
        assert (
            call(
                "startproject", self.project_name + "2", str(project_dir), cwd=tmp_path
            )
            == 1
        )
        assert call("startproject", "wrong---project---name") == 1
        assert call("startproject", "sys") == 1
        assert call("startproject") == 2
        assert (
            call("startproject", self.project_name, str(project_dir), "another_params")
            == 2
        )