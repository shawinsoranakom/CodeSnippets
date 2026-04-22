def test_should_cache_msg(self):
        """Test runtime_util.should_cache_msg"""
        with patch_config_options({"global.minCachedMessageSize": 0}):
            self.assertTrue(is_cacheable_msg(create_dataframe_msg([1, 2, 3])))

        with patch_config_options({"global.minCachedMessageSize": 1000}):
            self.assertFalse(is_cacheable_msg(create_dataframe_msg([1, 2, 3])))