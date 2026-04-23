def test_split_and_merge(self):
        x0 = torch.randn(128, d_hid)
        x1 = torch.randn(256, d_hid)
        x2 = torch.randn(512, d_hid)

        args = (x0, x1, x2)
        kwargs = {"x0": x0, "x1": x1, "x2": x2}

        # Default chunking: dim 0
        arg_chunks, kwarg_chunks = split_args_kwargs_into_chunks(args, kwargs, 2)
        if len(arg_chunks) != 2:
            raise AssertionError(f"Expected 2 arg_chunks, got {len(arg_chunks)}")
        if len(kwarg_chunks) != 2:
            raise AssertionError(f"Expected 2 kwarg_chunks, got {len(kwarg_chunks)}")
        if arg_chunks[0][0].shape != torch.Size([64, d_hid]):
            raise AssertionError(
                f"Expected arg_chunks[0][0].shape == [64, {d_hid}], got {arg_chunks[0][0].shape}"
            )
        if arg_chunks[1][0].shape != torch.Size([64, d_hid]):
            raise AssertionError(
                f"Expected arg_chunks[1][0].shape == [64, {d_hid}], got {arg_chunks[1][0].shape}"
            )
        if arg_chunks[0][1].shape != torch.Size([128, d_hid]):
            raise AssertionError(
                f"Expected arg_chunks[0][1].shape == [128, {d_hid}], got {arg_chunks[0][1].shape}"
            )
        if arg_chunks[0][2].shape != torch.Size([256, d_hid]):
            raise AssertionError(
                f"Expected arg_chunks[0][2].shape == [256, {d_hid}], got {arg_chunks[0][2].shape}"
            )
        if kwarg_chunks[0]["x0"].shape != torch.Size([64, d_hid]):
            raise AssertionError(
                f"Expected kwarg_chunks[0]['x0'].shape == [64, {d_hid}], got {kwarg_chunks[0]['x0'].shape}"
            )
        if kwarg_chunks[0]["x1"].shape != torch.Size([128, d_hid]):
            raise AssertionError(
                f"Expected kwarg_chunks[0]['x1'].shape == [128, {d_hid}], got {kwarg_chunks[0]['x1'].shape}"
            )
        if kwarg_chunks[1]["x2"].shape != torch.Size([256, d_hid]):
            raise AssertionError(
                f"Expected kwarg_chunks[1]['x2'].shape == [256, {d_hid}], got {kwarg_chunks[1]['x2'].shape}"
            )

        # Merge chunks back together
        merged_args = merge_chunks(
            arg_chunks,
            (TensorChunkSpec(0), TensorChunkSpec(0), TensorChunkSpec(0)),
        )
        torch.testing.assert_close(merged_args, args)

        merged_kwargs = merge_chunks(
            kwarg_chunks,
            {
                "x0": TensorChunkSpec(0),
                "x1": TensorChunkSpec(0),
                "x2": TensorChunkSpec(0),
            },
        )
        torch.testing.assert_close(merged_kwargs, kwargs)
        print("Microbatch test passed")