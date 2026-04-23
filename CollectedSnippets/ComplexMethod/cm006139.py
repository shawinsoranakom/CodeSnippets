async def test_s3_upload_list_delete_multiple_files(self, s3_files_client, s3_files_created_api_key):
        """Test uploading, listing, and deleting multiple files with S3 storage."""
        headers = {"x-api-key": s3_files_created_api_key.api_key}

        # Upload two files
        response1 = await s3_files_client.post(
            "api/v2/files",
            files={"file": ("s3_file1.txt", b"S3 content1")},
            headers=headers,
        )
        assert response1.status_code == 201
        file1 = response1.json()

        response2 = await s3_files_client.post(
            "api/v2/files",
            files={"file": ("s3_file2.txt", b"S3 content2")},
            headers=headers,
        )
        assert response2.status_code == 201
        file2 = response2.json()

        # List files and validate both are present
        response = await s3_files_client.get("api/v2/files", headers=headers)
        assert response.status_code == 200
        files = response.json()
        file_names = [f["name"] for f in files]
        file_ids = [f["id"] for f in files]
        assert file1["name"] in file_names
        assert file2["name"] in file_names
        assert file1["id"] in file_ids
        assert file2["id"] in file_ids

        # Delete one file
        response = await s3_files_client.delete(f"api/v2/files/{file1['id']}", headers=headers)
        assert response.status_code == 200

        # List files again and validate only the other remains
        response = await s3_files_client.get("api/v2/files", headers=headers)
        assert response.status_code == 200
        files = response.json()
        file_names = [f["name"] for f in files]
        file_ids = [f["id"] for f in files]
        assert file1["name"] not in file_names
        assert file1["id"] not in file_ids
        assert file2["name"] in file_names
        assert file2["id"] in file_ids