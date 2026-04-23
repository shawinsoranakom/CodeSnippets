def django_test_skips(self):
        skips = {
            "opclasses are PostgreSQL only.": {
                "indexes.tests.SchemaIndexesNotPostgreSQLTests."
                "test_create_index_ignores_opclasses",
            },
            "PostgreSQL requires casting to text.": {
                "lookup.tests.LookupTests.test_textfield_exact_null",
            },
        }
        if self.connection.settings_dict["OPTIONS"].get("pool"):
            skips.update(
                {
                    "Pool does implicit health checks": {
                        "backends.base.test_base.ConnectionHealthChecksTests."
                        "test_health_checks_enabled",
                        "backends.base.test_base.ConnectionHealthChecksTests."
                        "test_set_autocommit_health_checks_enabled",
                    },
                }
            )
        if self.uses_server_side_binding:
            skips.update(
                {
                    "The actual query cannot be determined for server side bindings": {
                        "backends.base.test_base.ExecuteWrapperTests."
                        "test_wrapper_debug",
                    }
                },
            )
        return skips