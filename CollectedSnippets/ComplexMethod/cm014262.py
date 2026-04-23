def compile_fn(
        self,
        gm: fx.GraphModule,
        example_inputs: list[torch.Tensor],
        **compiler_configs: Any,
    ) -> CompiledFn:
        """
        Implements graph splitting, first determining a set of buckets by counting
        parameter sizes in reverse graph order, then invoking the user/backend compiler
        to compile each subgraph. Finally, stitches compiled graphs into one graphmodule
        and returns its callable.
        """
        # 1: compute the partition map according to DDP bucket logic
        buckets = [Bucket()]  # (size, param_names)
        processed_modules: set[torch.nn.Module] = set()
        for node in reversed(gm.graph.nodes):
            if node.op in ("output", "placeholder"):
                continue

            if (
                buckets[0].size >= self.bucket_bytes_cap
                or len(buckets) == 1
                and buckets[0].size >= self.first_bucket_cap
            ):
                if bucket_has_external_output(buckets[0]):
                    buckets.insert(0, Bucket())
                else:
                    # continue building this bucket past the point of filling its parameter capacity,
                    # to increase chances it contains at least one node that is either a global output or
                    # passed as input to a subsequent graph

                    if buckets[0].opcount_increased_to_capture_external_output == 0:
                        buckets[0].paramsize_before_opcount_increase = buckets[0].size
                    buckets[0].opcount_increased_to_capture_external_output += 1

            if node.op == "call_function":
                self.add_param_args(buckets[0], node)

            elif node.op == "call_module":
                target_mod = gm.get_submodule(node.target)
                if target_mod not in processed_modules:
                    self.add_module_params_to_bucket(
                        target_mod, buckets[0], processed_modules, node.target
                    )
            elif node.op == "call_method":
                if isinstance(node.args[0].target, str):
                    target_mod = None
                    try:
                        target_mod = gm.get_submodule(node.args[0].target)
                    except AttributeError:
                        pass
                    if target_mod is not None and target_mod not in processed_modules:
                        self.add_module_params_to_bucket(
                            target_mod, buckets[0], processed_modules, node.target
                        )
                    # This handles situations like  tmp = torch.mm(x, self.weight.t())
                    # t: "f32[512, 512]" = l_self_seq_2_weight.t();  l_self_seq_2_weight = None
                    # tmp: "f32[512, 512]" = torch.mm(input_2, t);  input_2 = t = None
                    self.add_param_args(buckets[0], node)

            elif node.op == "get_attr":
                maybe_param = getattr(gm, node.target)
                if (
                    isinstance(maybe_param, torch.nn.Parameter)
                    and maybe_param.requires_grad
                    and not self._ignore_parameter(maybe_param)
                ):
                    self.add_param(buckets[0], maybe_param, node.target)

            # All nodes have to be mapped to a bucket, even if they don't have their own params
            # Ignored params still end up in buckets, we just don't count them towards the capacity
            buckets[0].nodes.append(node)

        if len(buckets) > 1 and buckets[0].size == 0:
            # we collected a small preamble graph with ops that don't include parameters, fuse it back
            buckets[1].nodes.extend(buckets[0].nodes)
            assert len(buckets[0].params) == 0, "Params should be empty if size is 0"
            del buckets[0]

        # stash buckets for testing/debugging purposes
        self.buckets = buckets
        pretty_print_buckets(buckets, self.bucket_bytes_cap)

        if len(buckets) == 1:
            # bypass split/fuse logic if there is only one bucket
            return self.backend_compile_fn(gm, example_inputs, **compiler_configs)

        # 2: partition the graphmodule according to bucket capacity
        partition_map = {}
        for idx, b in enumerate(buckets):
            for node in b.nodes:
                partition_map[node] = idx

        split_gm = fx.passes.split_module.split_module(
            gm,
            None,  # type: ignore[arg-type]
            lambda node: partition_map[node],
        )

        # See note [Assumption on Dynamo Metadata]
        propagate_dynamo_source(gm, split_gm)
        propagate_metadata(gm, split_gm)

        debug_str = (
            f"\n---orig graph---\n{gm.graph}\n"
            + f"\n---split graph---\n{split_gm.graph}\n"
        )
        for name, module in split_gm.named_modules():
            if "." not in name and len(name):
                # only print the submod graphs, not their children
                debug_str += f"\n---{name} graph---\n{module.graph}\n"
        debug_str += "\n---------------\n"
        ddp_graph_log.debug(debug_str)

        trace_structured(
            "optimize_ddp_split_graph",
            payload_fn=lambda: split_gm.print_readable(print_output=False),
        )
        for name, module in split_gm.named_modules():
            if "." not in name and len(name):
                trace_structured(
                    "optimize_ddp_split_child",
                    lambda: {"name": name},
                    payload_fn=lambda: module.print_readable(print_output=False),
                )

        fake_mode = detect_fake_mode(example_inputs)
        if fake_mode is None:
            fake_mode = torch._subclasses.fake_tensor.FakeTensorMode()

        submod_compiler = SubmodCompiler(
            split_gm, self.backend_compile_fn, fake_mode, **compiler_configs
        )
        with torch._dynamo.utils._disable_saved_tensors_hooks_during_tracing():
            submod_compiler.run(*example_inputs)
        split_gm.recompile()

        ddp_graph_log.debug(
            "\n---final graph---\n%s\n---------------\n", split_gm.graph
        )
        return split_gm