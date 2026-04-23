def test_keywords(self, client, params, expected_num, expected_message):
        if expected_message:
            with pytest.raises(Exception) as exception_info:
                client.list_chats(**params)
            assert expected_message in str(exception_info.value)
        else:
            assistants = client.list_chats(**params)
            if params["keywords"] in [None, ""]:
                assert len(assistants) == expected_num
            else:
                assert len(assistants) == expected_num
                if expected_num:
                    assert assistants[0].name == params["keywords"]