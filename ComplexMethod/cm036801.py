async def test_basic_score_and_response_structure(self, server: RemoteOpenAIServer):
        """Test basic generative scoring request and verify response structure."""
        response = requests.post(
            server.url_for("generative_scoring"),
            json={
                "model": MODEL_NAME,
                "query": "Is Paris the capital of France? Answer Yes or No: ",
                "items": ["Paris is beautiful.", "London is rainy."],
                "label_token_ids": [9454, 2753],
            },
        )
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()

        # Verify response structure
        assert data["id"].startswith("generative-scoring-")
        assert data["object"] == "list"
        assert "model" in data
        assert "usage" in data
        assert len(data["data"]) == 2

        # Verify each result
        for i, result in enumerate(data["data"]):
            assert result["index"] == i
            assert result["object"] == "score"
            assert 0.0 <= result["score"] <= 1.0

        # Verify usage tracking
        usage = data["usage"]
        assert usage["prompt_tokens"] > 0
        assert usage["completion_tokens"] > 0
        assert (
            usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
        )