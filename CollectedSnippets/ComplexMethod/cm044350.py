def test_output_status(model_fixture: Model,
                       steps: int,
                       current_step: int,
                       action: str,
                       mocker: pytest_mock.MockerFixture) -> None:
    """ Test that information is output correctly """
    mock_logger = mocker.patch("lib.training.lr_warmup.logger.info")
    mock_print = mocker.patch("builtins.print")
    instance = LearningRateWarmup(model_fixture, 5e-5, steps)
    instance._current_step = current_step
    instance._format_notation = mocker.MagicMock()  # type:ignore[method-assign]

    instance._output_status()

    if action == "unreported":
        assert current_step not in instance._reporting_points
        mock_logger.assert_not_called()
        instance._format_notation.assert_not_called()  # type:ignore[attr-defined]
        mock_print.assert_not_called()
        return

    mock_logger.assert_called_once()
    log_message: str = mock_logger.call_args.args[0]
    assert log_message.startswith("[Learning Rate Warmup] ")

    instance._format_notation.assert_called()  # type:ignore[attr-defined]
    notation_args = [
        x.args for x in instance._format_notation.call_args_list]  # type:ignore[attr-defined]
    assert all(len(a) == 1 for a in notation_args)
    assert all(isinstance(a[0], float) for a in notation_args)

    if action == "start":
        mock_print.assert_not_called()
        assert all(x in log_message for x in ("Start: ", "Target: ", "Steps: "))
        assert instance._format_notation.call_count == 2  # type:ignore[attr-defined]
        return

    if action == "end":
        mock_print.assert_called()
        assert "Final Learning Rate: " in log_message
        instance._format_notation.assert_called_once()  # type:ignore[attr-defined]
        return

    if action == "reported":
        mock_print.assert_called()
        assert current_step in instance._reporting_points
        assert all(x in log_message for x in ("Step: ", "Current: ", "Target: "))
        assert instance._format_notation.call_count == 2