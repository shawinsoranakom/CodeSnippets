async def test_get_transactions_response_structure(self, client: AsyncClient, logged_in_headers):
        """Test that transaction response items have the expected structure."""
        flow_id = uuid4()
        response = await client.get(f"api/v1/monitor/transactions?flow_id={flow_id}", headers=logged_in_headers)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        # Verify pagination structure
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert "pages" in result
        assert isinstance(result["items"], list)