def _get_stmt(
    benchmark: GroupedBenchmark,
    runtime: RuntimeMode,
    autograd: AutogradMode,
    language: Language,
) -> str | None:
    """Specialize a GroupedBenchmark for a particular configuration."""
    is_python = language == Language.PYTHON

    # During GroupedBenchmark construction, py_fwd_stmt and cpp_fwd_stmt are
    # set to the eager invocation. So in the RuntimeMode.EAGER case we can
    # simply reuse them. For the RuntimeMode.JIT case, we need to generate
    # an appropriate `jit_model(...)` invocation.
    if runtime == RuntimeMode.EAGER:
        stmts = (benchmark.py_fwd_stmt, benchmark.cpp_fwd_stmt)

    else:
        if runtime != RuntimeMode.JIT:
            raise AssertionError(f"Expected RuntimeMode.JIT, but got {runtime}")
        if benchmark.signature_args is None:
            raise AssertionError(
                "benchmark.signature_args must not be None for JIT mode"
            )
        stmts = GroupedBenchmark._make_model_invocation(
            benchmark.signature_args, benchmark.signature_output, RuntimeMode.JIT
        )

    stmt = stmts[0 if is_python else 1]

    if autograd == AutogradMode.FORWARD_BACKWARD and stmt is not None:
        if benchmark.signature_output is None:
            raise AssertionError(
                "benchmark.signature_output must not be None for FORWARD_BACKWARD mode"
            )
        backward = (
            f"{benchmark.signature_output}"
            # In C++ we have to get the Tensor out of the IValue to call `.backward()`
            f"{'.toTensor()' if runtime == RuntimeMode.JIT and language == Language.CPP else ''}"
            f".backward(){';' if language == Language.CPP else ''}"
        )
        stmt = f"{stmt}\n{backward}"
    return stmt