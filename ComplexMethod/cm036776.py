def test_turn_metrics_copy_and_reset():
    """Test TurnMetrics copy and reset methods work correctly."""
    # Create a TurnMetrics with specific values
    original_metrics = TurnMetrics(
        input_tokens=10,
        output_tokens=20,
        cached_input_tokens=5,
        tool_output_tokens=3,
    )

    # Test copy functionality
    copied_metrics = original_metrics.copy()

    # Verify copy has same values
    assert copied_metrics.input_tokens == 10
    assert copied_metrics.output_tokens == 20
    assert copied_metrics.cached_input_tokens == 5
    assert copied_metrics.tool_output_tokens == 3

    # Verify they are separate objects
    assert copied_metrics is not original_metrics

    # Modify copy to ensure independence
    copied_metrics.input_tokens = 999
    assert original_metrics.input_tokens == 10  # Original unchanged
    assert copied_metrics.input_tokens == 999

    # Test reset functionality
    original_metrics.reset()

    # Verify all fields are reset to zero
    assert original_metrics.input_tokens == 0
    assert original_metrics.output_tokens == 0
    assert original_metrics.cached_input_tokens == 0
    assert original_metrics.tool_output_tokens == 0

    # Verify copied metrics are unaffected by reset
    assert copied_metrics.input_tokens == 999
    assert copied_metrics.output_tokens == 20
    assert copied_metrics.cached_input_tokens == 5
    assert copied_metrics.tool_output_tokens == 3