def test_default_active_catalogs(self, project_dir):
        """Test that default catalogs are returned when no config exists."""
        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 2
        assert active[0].name == "default"
        assert active[0].priority == 1
        assert active[0].install_allowed is True
        assert active[1].name == "community"
        assert active[1].priority == 2
        assert active[1].install_allowed is False