def test_keywords(self, HttpApiAuth, params, expected_code, expected_num, expected_message):
        res = list_chat_assistants(HttpApiAuth, params=params)
        assert res["code"] == expected_code
        if expected_code == 0:
            if params["keywords"] in [None, ""]:
                assert len(_chat_list(res)) == expected_num
            else:
                assert len(_chat_list(res)) == expected_num
                if expected_num:
                    assert _chat_list(res)[0]["name"] == params["keywords"]
        else:
            assert res["message"] == expected_message