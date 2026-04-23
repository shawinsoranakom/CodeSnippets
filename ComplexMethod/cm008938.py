def test_multiple_middleware_can_modify_system_message(self) -> None:
        """Test that multiple middleware can modify system message in sequence."""

        def first_middleware(request: ModelRequest) -> ModelRequest:
            """First middleware adds base system message."""
            new_message = SystemMessage(
                content="You are an assistant.",
                additional_kwargs={"middleware_1": "applied"},
            )
            return request.override(system_message=new_message)

        def second_middleware(request: ModelRequest) -> ModelRequest:
            """Second middleware appends to system message."""
            assert request.system_message is not None
            current_content = request.system_message.text
            new_content = current_content + " Be helpful."

            merged_kwargs = {
                **request.system_message.additional_kwargs,
                "middleware_2": "applied",
            }

            new_message = SystemMessage(
                content=new_content,
                additional_kwargs=merged_kwargs,
            )
            return request.override(system_message=new_message)

        request = _make_request(system_message=None)

        # Apply middleware in sequence
        request = first_middleware(request)
        assert request.system_message is not None
        assert len(request.system_message.content_blocks) == 1
        assert request.system_message.content_blocks[0].get("text") == "You are an assistant."
        assert request.system_message.additional_kwargs["middleware_1"] == "applied"

        request = second_middleware(request)
        assert request.system_message is not None
        assert len(request.system_message.content_blocks) == 1
        assert (
            request.system_message.content_blocks[0].get("text")
            == "You are an assistant. Be helpful."
        )
        assert request.system_message.additional_kwargs["middleware_1"] == "applied"
        assert request.system_message.additional_kwargs["middleware_2"] == "applied"