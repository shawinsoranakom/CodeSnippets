def setUp(self):
        feature_patch_1 = patch.object(
            connection.features, "supports_tuple_lookups", False
        )
        feature_patch_2 = patch.object(
            connection.features, "supports_tuple_comparison_against_subquery", False
        )
        self.enterContext(feature_patch_1)
        self.enterContext(feature_patch_2)