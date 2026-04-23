def test_default_stack(self, temp_dir):
        """Default stack includes default and community catalogs."""
        project_dir = self._make_project(temp_dir)
        catalog = ExtensionCatalog(project_dir)

        entries = catalog.get_active_catalogs()

        assert len(entries) == 2
        assert entries[0].url == ExtensionCatalog.DEFAULT_CATALOG_URL
        assert entries[0].name == "default"
        assert entries[0].priority == 1
        assert entries[0].install_allowed is True
        assert entries[1].url == ExtensionCatalog.COMMUNITY_CATALOG_URL
        assert entries[1].name == "community"
        assert entries[1].priority == 2
        assert entries[1].install_allowed is False