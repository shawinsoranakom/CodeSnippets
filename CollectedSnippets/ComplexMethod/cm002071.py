def test_get_all_tests_on_full_repo(self):
        all_tests = get_all_tests()
        assert "tests/models/albert" in all_tests
        assert "tests/models/bert" in all_tests
        assert "tests/repo_utils" in all_tests
        assert "tests/test_pipeline_mixin.py" in all_tests
        assert "tests/models" not in all_tests
        assert "tests/__pycache__" not in all_tests
        assert "tests/models/albert/test_modeling_albert.py" not in all_tests
        assert "tests/repo_utils/test_tests_fetcher.py" not in all_tests