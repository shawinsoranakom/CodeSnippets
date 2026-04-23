def test_prompt(self, HttpApiAuth, add_chunks, prompt, expected_code, expected_message):
        dataset_id, _, _ = add_chunks
        payload = {"name": "prompt_test", "dataset_ids": [dataset_id]}
        prompt_config = {}
        for k, v in prompt.items():
            if k == "keywords_similarity_weight":
                payload["vector_similarity_weight"] = 1 - v
            elif k == "variables":
                prompt_config["parameters"] = v
            elif k == "opener":
                prompt_config["prologue"] = v
            elif k == "show_quote":
                prompt_config["quote"] = v
            elif k == "prompt":
                prompt_config["system"] = v
            elif k == "rerank_model":
                payload["rerank_id"] = v
            elif k in {"empty_response"}:
                prompt_config[k] = v
            else:
                payload[k] = v
        if prompt_config:
            payload["prompt_config"] = prompt_config
        res = create_chat_assistant(HttpApiAuth, payload)
        assert res["code"] == expected_code
        if expected_code == 0:
            if prompt:
                for k, v in prompt.items():
                    if k == "keywords_similarity_weight":
                        assert res["data"]["vector_similarity_weight"] == 1 - v
                    elif k == "variables":
                        expected_parameters = v
                        if not v and "{knowledge}" in res["data"]["prompt_config"]["system"]:
                            expected_parameters = [{"key": "knowledge", "optional": False}]
                        assert res["data"]["prompt_config"]["parameters"] == expected_parameters
                    elif k == "opener":
                        assert res["data"]["prompt_config"]["prologue"] == v
                    elif k == "show_quote":
                        assert res["data"]["prompt_config"]["quote"] == v
                    elif k == "prompt":
                        assert res["data"]["prompt_config"]["system"] == v
                    elif k == "rerank_model":
                        assert res["data"]["rerank_id"] == v
                    elif k == "empty_response":
                        assert res["data"]["prompt_config"]["empty_response"] == v
                    else:
                        assert res["data"][k] == v
            else:
                assert res["data"]["similarity_threshold"] == 0.1
                assert res["data"]["vector_similarity_weight"] == 0.3
                assert res["data"]["top_n"] == 6
                assert res["data"]["rerank_id"] == ""
                assert res["data"]["prompt_config"]["parameters"] == [{"key": "knowledge", "optional": False}]
                assert res["data"]["prompt_config"]["empty_response"] == "Sorry! No relevant content was found in the knowledge base!"
                assert res["data"]["prompt_config"]["prologue"] == "Hi! I'm your assistant. What can I do for you?"
                assert res["data"]["prompt_config"]["quote"] is True
                assert (
                    res["data"]["prompt_config"]["system"]
                    == 'You are an intelligent assistant. Please summarize the content of the dataset to answer the question. Please list the data in the dataset and answer in detail. When all dataset content is irrelevant to the question, your answer must include the sentence "The answer you are looking for is not found in the dataset!" Answers need to consider chat history.\n      Here is the knowledge base:\n      {knowledge}\n      The above is the knowledge base.'
                )
        else:
            assert res["message"] == expected_message