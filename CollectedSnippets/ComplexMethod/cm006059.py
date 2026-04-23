async def test_get_transactions_returns_paginated_response(self, client: AsyncClient, logged_in_headers):
        """Test that GET /monitor/transactions returns paginated response."""
        flow_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"api/v1/monitor/transactions?flow_id={flow_id}", headers=logged_in_headers)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "pages" in result
        assert isinstance(result["items"], list)