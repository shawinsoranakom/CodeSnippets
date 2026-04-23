def test_track_in_telemetry_field_exists(self):
        """Test that track_in_telemetry field exists in input classes."""
        from lfx.inputs.inputs import BoolInput, IntInput, SecretStrInput, StrInput

        # Regular input should default to False (opt-in model)
        regular_input = StrInput(name="test")
        assert hasattr(regular_input, "track_in_telemetry")
        assert regular_input.track_in_telemetry is False

        # Secret input should default to False
        secret_input = SecretStrInput(name="password")
        assert hasattr(secret_input, "track_in_telemetry")
        assert secret_input.track_in_telemetry is False

        # Safe inputs explicitly opt-in to tracking
        int_input = IntInput(name="count")
        assert hasattr(int_input, "track_in_telemetry")
        assert int_input.track_in_telemetry is True

        bool_input = BoolInput(name="flag")
        assert hasattr(bool_input, "track_in_telemetry")
        assert bool_input.track_in_telemetry is True