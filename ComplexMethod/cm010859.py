def _prepare_lazy_backward_context(self, saved_tensors_use_once: bool) -> None:
        if self.lazy_backward_info is None:
            raise AssertionError("lazy_backward_info must not be None")
        if not isinstance(self.lazy_backward_info, AutogradLazyBackwardCompileInfo):
            raise AssertionError(
                "expected AutogradLazyBackwardCompileInfo, "
                f"got {type(self.lazy_backward_info)}"
            )

        if (
            hasattr(self.lazy_backward_info, "saved_context")
            and self.lazy_backward_info.saved_context is not None
        ):
            if not isinstance(self.lazy_backward_info.saved_context, TracingContext):
                raise AssertionError(
                    f"expected TracingContext, got {type(self.lazy_backward_info.saved_context)}"
                )
            ddp_ctx = self.lazy_backward_info.saved_context.ddp_optimizer_ctx
            if ddp_ctx is not None:
                if ddp_ctx.curr_bucket < 0:
                    raise AssertionError(
                        "expected same # of fw and bw compiles, "
                        f"but found bucket {ddp_ctx.curr_bucket}"
                    )
                curr_fw_meta = ddp_ctx.metadata_per_bucket[ddp_ctx.curr_bucket]
                # Note [DDPOptimizer and fw_metadata]
                # When using the DDPOptimizer, we have a single dynamo graph (and TracingContext),
                # but multiple AOTDispatcher graph.
                #
                # One consequence is that there will be **multiple** fw_metadata objects, one per AOT graph,
                # which we stash the fw_metadata on the TracingContext.
                #
                # Normally what happens is that as we compile AOT graphs 1...N, we clobber the fw_metadata
                # for graph i-1 when we start running AOT for graph i.
                # Ordinarily this is fine, because inductor no longer needs the metadata from graph i-1.
                #
                # However, this is a problem for lazy compilation of the backward. During backward compilation,
                # we compile the backward lazily at backward runtime, meaning that we will first compile
                # backward graph N, N-1, ..., 1.
                # We need to ensure that at the time inductor compiles bw graph N-1, it can access
                # the corresponding fw_metadta for graph N-1.
                #
                # We do this by stashing a DDPOptimizerContext, which tracks:
                # - the metadata of all N graphs
                # - the graph we are currently compiling in our DDPOptimizer region.
                ddp_ctx.curr_bucket -= 1
                self.lazy_backward_info.saved_context.fw_metadata = curr_fw_meta

        if not saved_tensors_use_once:
            self.fw_metadata.bw_donated_idxs = []
            # Update bw_donated_idxs if using lazy_backward_info from `aot_dispatch_autograd`
            if (
                hasattr(self.lazy_backward_info, "saved_context")
                and hasattr(self.lazy_backward_info.saved_context, "fw_metadata")
                and hasattr(
                    self.lazy_backward_info.saved_context.fw_metadata,  # type: ignore[union-attr]
                    "bw_donated_idxs",
                )
            ):
                self.lazy_backward_info.saved_context.fw_metadata.bw_donated_idxs = (  # type: ignore[union-attr]
                    # pyrefly: ignore [implicit-any]
                    []
                )