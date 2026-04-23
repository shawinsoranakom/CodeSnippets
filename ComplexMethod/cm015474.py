def set_backward_prefetch(model: Transformer) -> None:
            # tell pyre model.set_modules_to_backward_prefetch is available
            if not isinstance(model, FSDPModule):
                raise AssertionError(f"Expected FSDPModule, got {type(model)}")
            if not isinstance(model.output, FSDPModule):
                raise AssertionError(f"Expected FSDPModule, got {type(model.output)}")

            # mimic deepseek MOE
            # prefetch layer - 1 and its feedforward before cpu sync during a2a
            reversed_transformer_blocks = list(reversed(model.layers))
            prev_transformer_blocks = reversed_transformer_blocks[1:] + [None]

            if (
                model.norm is not None
                and model.output is not None
                and len(model.layers) > 0
            ):
                if not isinstance(reversed_transformer_blocks[0], FSDPModule):
                    raise AssertionError(
                        f"Expected FSDPModule, got {type(reversed_transformer_blocks[0])}"
                    )
                model.output.set_modules_to_backward_prefetch(
                    [reversed_transformer_blocks[0]]
                )

            for transformer_block, prev_transformer_block in zip(
                reversed_transformer_blocks, prev_transformer_blocks
            ):
                if not isinstance(transformer_block, FSDPModule):
                    raise AssertionError(
                        f"Expected FSDPModule, got {type(transformer_block)}"
                    )
                if prev_transformer_block is not None:
                    if not isinstance(prev_transformer_block, FSDPModule):
                        raise AssertionError(
                            f"Expected FSDPModule, got {type(prev_transformer_block)}"
                        )
                    if not hasattr(prev_transformer_block.feed_forward, "w1"):
                        raise AssertionError(
                            "Expected prev_transformer_block.feed_forward to have 'w1' attribute"
                        )
                    if not isinstance(
                        prev_transformer_block.feed_forward.w1, FSDPModule
                    ):
                        raise AssertionError(
                            f"Expected FSDPModule, got {type(prev_transformer_block.feed_forward.w1)}"
                        )
                    transformer_block.set_modules_to_backward_prefetch(
                        [
                            prev_transformer_block,
                            prev_transformer_block.feed_forward.w1,
                        ]
                    )
                elif model.tok_embeddings is not None:
                    if not isinstance(model.tok_embeddings, FSDPModule):
                        raise AssertionError(
                            f"Expected FSDPModule, got {type(model.tok_embeddings)}"
                        )
                    transformer_block.set_modules_to_backward_prefetch(
                        [model.tok_embeddings]
                    )