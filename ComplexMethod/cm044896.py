def test_yaml_is_valid(self, tmp_path):
        """Every generated YAML file must parse without errors."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            # Strip trailing source comment before parsing
            lines = content.split("\n")
            yaml_lines = [l for l in lines if not l.startswith("# Source:")]
            try:
                parsed = yaml.safe_load("\n".join(yaml_lines))
            except Exception as exc:
                raise AssertionError(f"{f.name} is not valid YAML: {exc}") from exc
            assert "prompt" in parsed, f"{f.name} parsed YAML has no 'prompt' key"
            assert "title" in parsed, f"{f.name} parsed YAML has no 'title' key"