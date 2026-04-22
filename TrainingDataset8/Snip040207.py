def test_md5_calculation_succeeds_with_dir_input(self, mock_stable_dir_identifier):
        mock_stable_dir_identifier.return_value = "hello"

        md5 = util.calc_md5_with_blocking_retries("foo")
        self.assertEqual(md5, "5d41402abc4b2a76b9719d911017c592")
        mock_stable_dir_identifier.assert_called_once_with("foo", "*")