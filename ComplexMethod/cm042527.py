def _assert_files_exist(project_dir: Path, project_name: str) -> None:
        assert (project_dir / "scrapy.cfg").exists()
        assert (project_dir / project_name).exists()
        assert (project_dir / project_name / "__init__.py").exists()
        assert (project_dir / project_name / "items.py").exists()
        assert (project_dir / project_name / "pipelines.py").exists()
        assert (project_dir / project_name / "settings.py").exists()
        assert (project_dir / project_name / "spiders" / "__init__.py").exists()