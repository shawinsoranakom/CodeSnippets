def test_agent_crud_validation_contract(self, HttpApiAuth, agent_id):
        res = list_agents(HttpApiAuth, {"id": "missing-agent-id", "title": "missing-agent-title"})
        assert res["code"] == 102, res
        assert "doesn't exist" in res["message"], res

        res = list_agents(HttpApiAuth, {"title": AGENT_TITLE, "desc": "true", "page_size": 1})
        assert res["code"] == 0, res

        res = create_agent(HttpApiAuth, {"title": "missing-dsl-agent"})
        assert res["code"] == 101, res
        assert "No DSL data in request" in res["message"], res

        res = create_agent(HttpApiAuth, {"dsl": MINIMAL_DSL})
        assert res["code"] == 101, res
        assert "No title in request" in res["message"], res

        res = create_agent(HttpApiAuth, {"title": AGENT_TITLE, "dsl": MINIMAL_DSL})
        assert res["code"] == 102, res
        assert "already exists" in res["message"], res

        update_url = f"{HOST_ADDRESS}/api/{VERSION}/agents/invalid-agent-id"
        res = requests.put(update_url, auth=HttpApiAuth, json={"title": "updated", "dsl": MINIMAL_DSL}).json()
        assert res["code"] == 103, res
        assert "Only owner of canvas authorized" in res["message"], res

        res = delete_agent(HttpApiAuth, "invalid-agent-id")
        assert res["code"] == 103, res
        assert "Only owner of canvas authorized" in res["message"], res