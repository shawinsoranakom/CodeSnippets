async def test_s3_delete_file(self, s3_files_client, s3_files_created_api_key):
        """Test deleting a file from S3 storage (verifies delete bug fix)."""
        headers = {"x-api-key": s3_files_created_api_key.api_key}

        # Upload a file
        response = await s3_files_client.post(
            "api/v2/files",
            files={"file": ("s3_delete_test.txt", b"S3 delete content")},
            headers=headers,
        )
        assert response.status_code == 201
        upload_response = response.json()

        # Delete the file
        response = await s3_files_client.delete(f"api/v2/files/{upload_response['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"detail": "File s3_delete_test deleted successfully"}

        # Verify file is deleted from database
        response = await s3_files_client.get("api/v2/files", headers=headers)
        assert response.status_code == 200
        files = response.json()
        file_names = [f["name"] for f in files]
        assert "s3_delete_test" not in file_names

        # Verify file is deleted from S3 (should return 404)
        response = await s3_files_client.get(f"api/v2/files/{upload_response['id']}", headers=headers)
        assert response.status_code == 404