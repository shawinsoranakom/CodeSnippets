def modify_mock_file():
            self.util_mock.path_modification_time = lambda *args: mod_count[0]
            self.util_mock.calc_md5_with_blocking_retries = (
                lambda _, **kwargs: "%d" % mod_count[0]
            )

            mod_count[0] += 1.0