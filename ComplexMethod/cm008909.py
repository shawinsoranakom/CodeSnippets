async def test_aread_binary_file_100_kib(
        self, sandbox_backend: SandboxBackendProtocol, sandbox_test_root: str
    ) -> None:
        """Async read should return base64 content for a 100 KiB binary file."""
        if not self.has_async:
            pytest.skip("Async tests not supported.")

        test_path = self.sandbox_path(
            "async_binary_100kib.png", root_dir=sandbox_test_root
        )
        chunk = bytes(range(256))
        raw_bytes = chunk * 400

        upload_responses = await sandbox_backend.aupload_files([(test_path, raw_bytes)])
        assert upload_responses == [FileUploadResponse(path=test_path, error=None)]

        result = await sandbox_backend.aread(test_path)
        assert isinstance(result, ReadResult)
        assert result.error is None
        assert result.file_data is not None
        assert result.file_data["encoding"] == "base64"
        assert base64.b64decode(result.file_data["content"]) == raw_bytes