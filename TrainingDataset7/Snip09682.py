def test_collations(self):
        return {
            "ci": "BINARY_CI",
            "cs": "BINARY",
            "non_default": "SWEDISH_CI",
            "swedish_ci": "SWEDISH_CI",
            "virtual": "SWEDISH_CI" if self.supports_collation_on_charfield else None,
        }