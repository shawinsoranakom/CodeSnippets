def test_md5_calculation_allow_nonexistent(self):
        md5 = util.calc_md5_with_blocking_retries("hello", allow_nonexistent=True)
        self.assertEqual(md5, "5d41402abc4b2a76b9719d911017c592")