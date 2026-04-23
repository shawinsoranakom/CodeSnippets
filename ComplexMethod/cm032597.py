def test_pipeline_log_lifecycle(self, WebApiAuth, add_document):
        kb_id, document_id = add_document
        parse_documents(WebApiAuth, {"doc_ids": [document_id], "run": "1"})
        _wait_for_docs_parsed(WebApiAuth, kb_id)
        _wait_for_pipeline_logs(WebApiAuth, kb_id)

        list_res = kb_list_pipeline_logs(WebApiAuth, params={"kb_id": kb_id}, payload={})
        assert list_res["code"] == 0, list_res
        assert "total" in list_res["data"], list_res
        assert isinstance(list_res["data"]["logs"], list), list_res
        assert list_res["data"]["logs"], list_res

        log_id = list_res["data"]["logs"][0]["id"]
        detail_res = kb_pipeline_log_detail(WebApiAuth, {"log_id": log_id})
        assert detail_res["code"] == 0, detail_res
        detail = detail_res["data"]
        assert detail["id"] == log_id, detail_res
        assert detail["kb_id"] == kb_id, detail_res
        for key in ["document_id", "task_type", "operation_status", "progress"]:
            assert key in detail, detail_res

        delete_res = kb_delete_pipeline_logs(WebApiAuth, params={"kb_id": kb_id}, payload={"log_ids": [log_id]})
        assert delete_res["code"] == 0, delete_res
        assert delete_res["data"] is True, delete_res

        @wait_for(30, 1, "Pipeline log delete timeout")
        def _condition():
            res = kb_list_pipeline_logs(WebApiAuth, params={"kb_id": kb_id}, payload={})
            if res["code"] != 0:
                return False
            return all(log.get("id") != log_id for log in res["data"]["logs"])

        _condition()