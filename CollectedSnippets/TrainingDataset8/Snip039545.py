def test_mocks_do_not_result_in_infinite_recursion(self):
        try:
            get_hash(Mock())
            get_hash(MagicMock())
        except InternalHashError:
            self.fail("get_hash raised InternalHashError")