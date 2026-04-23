def test_real_world_api_response(self):
        """Test analysis of realistic API response structure."""
        api_response = {
            "status": "success",
            "data": {
                "users": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "created_at": "2023-01-15T10:30:00Z",
                        "metadata": {"login_count": 42, "preferences": {"theme": "dark", "notifications": True}},
                    },
                    {
                        "id": 2,
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "created_at": "2023-02-01T14:20:00Z",
                        "metadata": {"login_count": 15, "preferences": {"theme": "light", "notifications": False}},
                    },
                ],
                "pagination": {"page": 1, "per_page": 10, "total": 2},
            },
        }

        result = get_data_structure(api_response, include_sample_values=True, include_sample_structure=True)

        assert "structure" in result
        assert "samples" in result

        structure = result["structure"]
        assert structure["status"] == "str"
        assert "data" in structure
        assert "users" in structure["data"]
        assert "list(dict)" in structure["data"]["users"]

        # Check that pagination structure is captured
        pagination = structure["data"]["pagination"]
        assert pagination["page"] == "int"
        assert pagination["total"] == "int"