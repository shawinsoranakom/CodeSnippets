def test_md5_calculation_can_pass_glob(self, mock_stable_dir_identifier):
        mock_stable_dir_identifier.return_value = "hello"

        md5 = util.calc_md5_with_blocking_retries("foo", glob_pattern="*.py")
        mock_stable_dir_identifier.assert_called_once_with("foo", "*.py")