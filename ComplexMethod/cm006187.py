def test_payload_serialization_exclude_unset_fields(self):
        """Test that payloads can exclude unset fields during serialization."""
        payload = RunPayload(
            run_seconds=30,
            run_success=True,
            # run_is_webhook and run_error_message not set, will use defaults
        )

        # Standard serialization includes all fields
        full_serialization = payload.model_dump(by_alias=True)
        assert "runIsWebhook" in full_serialization
        assert "runErrorMessage" in full_serialization
        assert full_serialization["runIsWebhook"] is False
        assert full_serialization["runErrorMessage"] == ""

        # Exclude unset should only include explicitly set fields
        exclude_unset = payload.model_dump(by_alias=True, exclude_unset=True)
        assert "runSeconds" in exclude_unset
        assert "runSuccess" in exclude_unset
        # These have defaults but weren't set explicitly, so they're excluded
        assert "runIsWebhook" not in exclude_unset
        assert "runErrorMessage" not in exclude_unset
        assert "clientType" not in exclude_unset