def test_check_session_state_rules_no_key(self, patched_st_warning):
        check_session_state_rules(5, key=None)

        patched_st_warning.assert_not_called()