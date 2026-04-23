def test_merge_conflict_higher_priority_wins(self, temp_dir):
        """When same extension id is in two catalogs, higher priority wins."""
        project_dir = self._make_project(temp_dir)

        # Write project config with two catalogs
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "primary",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": True,
                },
                {
                    "name": "secondary",
                    "url": ExtensionCatalog.COMMUNITY_CATALOG_URL,
                    "priority": 2,
                    "install_allowed": False,
                },
            ],
        )

        catalog = ExtensionCatalog(project_dir)

        # Write primary cache with jira v2.0.0
        primary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "2.0.0",
                    "description": "Primary Jira",
                }
            },
        }
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(primary_data))
        catalog.cache_metadata_file.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": "http://test.com"})
        )

        # Write secondary cache (URL-hash-based) with jira v1.0.0 (should lose)
        import hashlib

        url_hash = hashlib.sha256(ExtensionCatalog.COMMUNITY_CATALOG_URL.encode()).hexdigest()[:16]
        secondary_cache = catalog.cache_dir / f"catalog-{url_hash}.json"
        secondary_meta = catalog.cache_dir / f"catalog-{url_hash}-metadata.json"
        secondary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration Community",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Community Jira",
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "0.9.0",
                    "description": "Linear from secondary",
                },
            },
        }
        secondary_cache.write_text(json.dumps(secondary_data))
        secondary_meta.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": ExtensionCatalog.COMMUNITY_CATALOG_URL})
        )

        results = catalog.search()
        jira_results = [r for r in results if r["id"] == "jira"]
        assert len(jira_results) == 1
        # Primary catalog wins
        assert jira_results[0]["version"] == "2.0.0"
        assert jira_results[0]["_catalog_name"] == "primary"
        assert jira_results[0]["_install_allowed"] is True

        # linear comes from secondary
        linear_results = [r for r in results if r["id"] == "linear"]
        assert len(linear_results) == 1
        assert linear_results[0]["_catalog_name"] == "secondary"
        assert linear_results[0]["_install_allowed"] is False