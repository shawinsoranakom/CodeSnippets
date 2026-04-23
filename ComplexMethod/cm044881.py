def test_valid_manifest(self, pack_dir):
        """Test loading a valid manifest."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert manifest.id == "test-pack"
        assert manifest.name == "Test Preset"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test preset"
        assert manifest.author == "Test Author"
        assert manifest.requires_speckit_version == ">=0.1.0"
        assert len(manifest.templates) == 1
        assert manifest.tags == ["testing", "example"]