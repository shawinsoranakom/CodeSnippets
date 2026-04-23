async def test_batch_delete_with_mixed_failures(self):
        """Test batch delete with mix of permanent and transient failures."""
        from langflow.services.database.models.file.model import File as UserFile

        user_id = uuid.uuid4()
        file_ids = [uuid.uuid4() for _ in range(3)]
        file_names = [f"batch_test_{i}.txt" for i in range(3)]

        mock_files = [
            UserFile(
                id=file_ids[i],
                user_id=user_id,
                name=file_names[i],
                path=f"{file_ids[i]}.txt",
                size=100,
            )
            for i in range(3)
        ]

        mock_current_user = MagicMock()
        mock_current_user.id = user_id

        mock_exec_result = MagicMock()
        mock_exec_result.all = MagicMock(return_value=mock_files)
        mock_session = AsyncMock()
        mock_session.exec = AsyncMock(return_value=mock_exec_result)
        mock_session.delete = AsyncMock()

        deleted_file_ids = set()

        async def mock_delete_file(*, flow_id: str | None = None, file_name: str | None = None) -> None:  # noqa: ARG001
            if file_name == f"{file_ids[0]}.txt":
                msg = f"File {file_name} not found"
                raise FileNotFoundError(msg)
            if file_name == f"{file_ids[1]}.txt":
                msg = "Network error"
                raise ConnectionError(msg)
            deleted_file_ids.add(file_name)

        mock_storage_service = AsyncMock()
        mock_storage_service.delete_file = AsyncMock(side_effect=mock_delete_file)

        result = await delete_files_batch(
            file_ids=file_ids,
            current_user=mock_current_user,
            session=mock_session,
            storage_service=mock_storage_service,
        )

        assert (
            result["message"]
            == "2 files deleted successfully, 1 files kept in database due to transient storage errors (can retry)"
        )

        assert mock_storage_service.delete_file.call_count == 3

        delete_calls = [call[0][0] for call in mock_session.delete.call_args_list]
        assert len(delete_calls) == 2
        assert mock_files[0] in delete_calls
        assert mock_files[2] in delete_calls
        assert mock_files[1] not in delete_calls