def test_parse_commit_message(self):
        assert parse_commit_message("Normal commit") == {"skip": False, "no_filter": False, "test_all": False}

        assert parse_commit_message("[skip ci] commit") == {"skip": True, "no_filter": False, "test_all": False}
        assert parse_commit_message("[ci skip] commit") == {"skip": True, "no_filter": False, "test_all": False}
        assert parse_commit_message("[skip-ci] commit") == {"skip": True, "no_filter": False, "test_all": False}
        assert parse_commit_message("[skip_ci] commit") == {"skip": True, "no_filter": False, "test_all": False}

        assert parse_commit_message("[no filter] commit") == {"skip": False, "no_filter": True, "test_all": False}
        assert parse_commit_message("[no-filter] commit") == {"skip": False, "no_filter": True, "test_all": False}
        assert parse_commit_message("[no_filter] commit") == {"skip": False, "no_filter": True, "test_all": False}
        assert parse_commit_message("[filter-no] commit") == {"skip": False, "no_filter": True, "test_all": False}

        assert parse_commit_message("[test all] commit") == {"skip": False, "no_filter": False, "test_all": True}
        assert parse_commit_message("[all test] commit") == {"skip": False, "no_filter": False, "test_all": True}
        assert parse_commit_message("[test-all] commit") == {"skip": False, "no_filter": False, "test_all": True}
        assert parse_commit_message("[all_test] commit") == {"skip": False, "no_filter": False, "test_all": True}