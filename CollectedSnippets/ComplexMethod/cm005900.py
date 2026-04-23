def test_should_include_all_optional_fields(self):
        """Should include all optional fields when provided."""
        result = format_progress_event(
            "validation_failed",
            2,
            4,
            message="Validation failed",
            error="SyntaxError",
            class_name="BrokenComponent",
            component_code="class Broken: pass",
        )

        data = json.loads(result[6:-2])

        assert data["event"] == "progress"
        assert data["step"] == "validation_failed"
        assert data["attempt"] == 2
        assert data["max_attempts"] == 4
        assert data["message"] == "Validation failed"
        assert data["error"] == "SyntaxError"
        assert data["class_name"] == "BrokenComponent"
        assert data["component_code"] == "class Broken: pass"