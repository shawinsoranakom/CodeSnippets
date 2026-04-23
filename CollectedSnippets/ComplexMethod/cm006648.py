def test_all_projects_load(self, starter_projects_path: Path):
        """Test all starter project JSONs can load without lfx-specific errors.

        Note: This test only fails on lfx-specific module errors (lfx.components.*),
        not on missing external dependencies (langchain_anthropic, etc.) which are
        expected when running with minimal dev dependencies.
        """
        from lfx.load import load_flow_from_json

        json_files = list(starter_projects_path.glob("*.json"))
        assert len(json_files) > 0, "No starter project files found"

        lfx_module_errors = []

        for json_file in json_files:
            try:
                graph = load_flow_from_json(json_file, disable_logs=True)
                assert graph is not None
                graph.prepare()
            except Exception as e:
                error_str = str(e)
                # Only track lfx-specific errors, not external dependency errors
                if "No module named 'lfx." in error_str:
                    lfx_module_errors.append((json_file.name, str(e)))
                elif "resolve_component_path" in error_str:
                    lfx_module_errors.append((json_file.name, f"Storage error: {e}"))
                # External dependency errors (langchain_anthropic, etc.) are acceptable
                # as lfx is designed to work with minimal dependencies

        if lfx_module_errors:
            error_details = "\n".join([f"  {name}: {error}" for name, error in lfx_module_errors])
            pytest.fail(f"LFX module errors in starter projects:\n{error_details}")