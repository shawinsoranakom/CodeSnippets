def test_supports_args_runtime_dispatch_and_warning(
        self, caplog_vllm: pytest.LogCaptureFixture
    ):
        x1 = torch.ones((2, 2), dtype=torch.int32)
        y1 = torch.full((2, 2), 2, dtype=torch.int32)

        x2 = torch.ones((2, 3), dtype=torch.int32)
        y2 = torch.full((2, 3), 2, dtype=torch.int32)

        with (
            caplog_vllm.at_level(logging.WARNING),
            _custom_add.set_priority(["impl_even"]),
        ):
            # Test the warning about native fallback is logged (before even dispatching)
            assert len(caplog_vllm.records) == 1
            message = caplog_vllm.records[0].message
            assert "_custom_add" in message
            assert "fallback to native" in message
            assert "priority" in message

            # Check dispatching
            assert _custom_add.get_priority() == ["impl_even", "native"]
            assert _custom_add.dispatch(x1, y1) is impl_even
            assert _custom_add.dispatch(x2, y2) is _custom_add.impls["native"]

            out1 = _custom_add(x1, y1)  # size(1) == 2 → impl_even
            out2 = _custom_add(x2, y2)  # size(1) == 3 → native fallback

        # no other warnings
        assert len(caplog_vllm.records) == 1
        assert torch.all(out1 == 1 + 2 + 50)
        assert torch.all(out2 == 1 + 2)