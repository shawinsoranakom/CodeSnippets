def test_build_start_emitted_before_exception(self):
        """Verify build_start is emitted before the exception, and both events are present."""
        from unittest.mock import MagicMock, patch

        from lfx.events.event_manager import create_default_event_manager

        calculator_component = CalculatorToolComponent(_id="test-exception-component-id")

        mock_queue = MagicMock()
        event_manager = create_default_event_manager(queue=mock_queue)
        calculator_component.set_event_manager(event_manager)

        component_toolkit = ComponentToolkit(component=calculator_component)
        component_tool = component_toolkit.get_tools()[0]

        with patch.object(CalculatorToolComponent, "run_model", side_effect=ValueError("boom")):
            # handle_tool_error=True means ToolException is caught and returned as string
            component_tool.invoke(input={"expression": "1+1"})

        all_events = [call[0][0][1] for call in mock_queue.put_nowait.call_args_list]
        event_types = [
            next(t for t in (b"build_start", b"build_end") if t in ev)
            for ev in all_events
            if b"build_start" in ev or b"build_end" in ev
        ]
        assert event_types == [b"build_start", b"build_end"], "build_start must precede build_end"