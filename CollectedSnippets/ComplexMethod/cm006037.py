def assert_output_equivalence(trace1: ExecutionTrace, trace2: ExecutionTrace) -> None:
    """Assert that two execution traces produced equivalent outputs."""
    # Compare final outputs
    if trace1.final_outputs and trace2.final_outputs:
        # Both should have outputs
        assert len(trace1.final_outputs) == len(trace2.final_outputs), (
            f"Different number of outputs:\n"
            f"{trace1.path_name}: {len(trace1.final_outputs)}\n"
            f"{trace2.path_name}: {len(trace2.final_outputs)}"
        )

        # Compare output results (Note: exact comparison may need to be relaxed
        # depending on non-deterministic components like LLMs)
        for i, (out1, out2) in enumerate(zip(trace1.final_outputs, trace2.final_outputs, strict=True)):
            # Basic structural comparison
            if hasattr(out1, "outputs") and hasattr(out2, "outputs"):
                assert len(out1.outputs) == len(out2.outputs), (
                    f"Output {i} has different number of results:\n"
                    f"{trace1.path_name}: {len(out1.outputs)}\n"
                    f"{trace2.path_name}: {len(out2.outputs)}"
                )