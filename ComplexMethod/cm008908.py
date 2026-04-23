async def test_aread_binary_image_file(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Async read should return base64-encoded content for a binary image file."""
        if not self.has_async:
            pytest.skip("Async tests not supported.")

        test_path = self.sandbox_path("async_binary.png", root_dir=sandbox_test_root)
        raw_bytes = bytes(range(256))

        upload_responses = await sandbox_backend.aupload_files([(test_path, raw_bytes)])
        assert upload_responses == [FileUploadResponse(path=test_path, error=None)]

        result = await sandbox_backend.aread(test_path)
        assert isinstance(result, ReadResult)
        assert result.error is None
        assert result.file_data is not None
        assert result.file_data["encoding"] == "base64"
        assert base64.b64decode(result.file_data["content"]) == raw_bytes