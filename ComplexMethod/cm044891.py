def test_setup_creates_files(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        skill_files = [f for f in created if "scripts" not in f.parts]
        for f in skill_files:
            assert f.exists()
            assert f.name == "SKILL.md"
            assert f.parent.name.startswith("speckit-")