def test_update_to_true(self, WebApiAuth):
        memory_id = self.memory_id
        list_res = list_memory_message(WebApiAuth, memory_id)
        assert list_res["code"] == 0, list_res
        assert len(list_res["data"]["messages"]["message_list"]) > 0
        # set 1 random message to false first
        message = random.choice(list_res["data"]["messages"]["message_list"])
        set_to_false_res = update_message_status(WebApiAuth, memory_id, message["message_id"], False)
        assert set_to_false_res["code"] == 0, set_to_false_res
        updated_message_res = get_message_content(WebApiAuth, memory_id, message["message_id"])
        assert updated_message_res["code"] == 0, set_to_false_res
        assert not updated_message_res["data"]["status"], updated_message_res
        # set to true
        set_to_true_res = update_message_status(WebApiAuth, memory_id, message["message_id"], True)
        assert set_to_true_res["code"] == 0, set_to_true_res
        res = get_message_content(WebApiAuth, memory_id, message["message_id"])
        assert res["code"] == 0, res
        assert res["data"]["status"], res