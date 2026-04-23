def test_seq_batch_return_exceptions(mocker: MockerFixture) -> None:
    class ControlledExceptionRunnable(Runnable[str, str]):
        def __init__(self, fail_starts_with: str) -> None:
            self.fail_starts_with = fail_starts_with

        @override
        def invoke(
            self, input: Any, config: RunnableConfig | None = None, **kwargs: Any
        ) -> Any:
            raise NotImplementedError

        def _batch(
            self,
            inputs: list[str],
        ) -> list[str | Exception]:
            outputs: list[str | Exception] = []
            for value in inputs:
                if value.startswith(self.fail_starts_with):
                    outputs.append(
                        ValueError(
                            f"ControlledExceptionRunnable({self.fail_starts_with}) "
                            f"fail for {value}"
                        )
                    )
                else:
                    outputs.append(value + "a")
            return outputs

        def batch(
            self,
            inputs: list[str],
            config: RunnableConfig | list[RunnableConfig] | None = None,
            *,
            return_exceptions: bool = False,
            **kwargs: Any,
        ) -> list[str]:
            return self._batch_with_config(
                self._batch,
                inputs,
                config,
                return_exceptions=return_exceptions,
                **kwargs,
            )

    chain = (
        ControlledExceptionRunnable("bux")
        | ControlledExceptionRunnable("bar")
        | ControlledExceptionRunnable("baz")
        | ControlledExceptionRunnable("foo")
    )

    assert isinstance(chain, RunnableSequence)

    # Test batch
    with pytest.raises(
        ValueError, match=re.escape("ControlledExceptionRunnable(bar) fail for bara")
    ):
        chain.batch(["foo", "bar", "baz", "qux"])

    spy = mocker.spy(ControlledExceptionRunnable, "batch")
    tracer = FakeTracer()
    inputs = ["foo", "bar", "baz", "qux"]
    outputs = chain.batch(inputs, {"callbacks": [tracer]}, return_exceptions=True)
    assert len(outputs) == 4
    assert isinstance(outputs[0], ValueError)
    assert isinstance(outputs[1], ValueError)
    assert isinstance(outputs[2], ValueError)
    assert outputs[3] == "quxaaaa"
    assert spy.call_count == 4
    inputs_to_batch = [c[0][1] for c in spy.call_args_list]
    assert inputs_to_batch == [
        # inputs to sequence step 0
        # same as inputs to sequence.batch()
        ["foo", "bar", "baz", "qux"],
        # inputs to sequence step 1
        # == outputs of sequence step 0 as no exceptions were raised
        ["fooa", "bara", "baza", "quxa"],
        # inputs to sequence step 2
        # 'bar' was dropped as it raised an exception in step 1
        ["fooaa", "bazaa", "quxaa"],
        # inputs to sequence step 3
        # 'baz' was dropped as it raised an exception in step 2
        ["fooaaa", "quxaaa"],
    ]
    parent_runs = sorted(
        (r for r in tracer.runs if r.parent_run_id is None),
        key=lambda run: inputs.index(run.inputs["input"]),
    )
    assert len(parent_runs) == 4

    parent_run_foo = parent_runs[0]
    assert parent_run_foo.inputs["input"] == "foo"
    assert repr(ValueError("ControlledExceptionRunnable(foo) fail for fooaaa")) in str(
        parent_run_foo.error
    )
    assert len(parent_run_foo.child_runs) == 4
    assert [r.error for r in parent_run_foo.child_runs[:-1]] == [
        None,
        None,
        None,
    ]
    assert repr(ValueError("ControlledExceptionRunnable(foo) fail for fooaaa")) in str(
        parent_run_foo.child_runs[-1].error
    )

    parent_run_bar = parent_runs[1]
    assert parent_run_bar.inputs["input"] == "bar"
    assert repr(ValueError("ControlledExceptionRunnable(bar) fail for bara")) in str(
        parent_run_bar.error
    )
    assert len(parent_run_bar.child_runs) == 2
    assert parent_run_bar.child_runs[0].error is None
    assert repr(ValueError("ControlledExceptionRunnable(bar) fail for bara")) in str(
        parent_run_bar.child_runs[1].error
    )

    parent_run_baz = parent_runs[2]
    assert parent_run_baz.inputs["input"] == "baz"
    assert repr(ValueError("ControlledExceptionRunnable(baz) fail for bazaa")) in str(
        parent_run_baz.error
    )
    assert len(parent_run_baz.child_runs) == 3

    assert [r.error for r in parent_run_baz.child_runs[:-1]] == [
        None,
        None,
    ]
    assert repr(ValueError("ControlledExceptionRunnable(baz) fail for bazaa")) in str(
        parent_run_baz.child_runs[-1].error
    )

    parent_run_qux = parent_runs[3]
    assert parent_run_qux.inputs["input"] == "qux"
    assert parent_run_qux.error is None
    assert parent_run_qux.outputs is not None
    assert parent_run_qux.outputs["output"] == "quxaaaa"
    assert len(parent_run_qux.child_runs) == 4
    assert [r.error for r in parent_run_qux.child_runs] == [None, None, None, None]