def copy_paste_aot_backward_graph() -> list[torch.Tensor]:
            def num_inputs(graph: torch.fx.Graph) -> int:
                num_args = 0
                for node in graph.nodes:
                    if node.op == "placeholder":
                        num_args += 1
                        continue
                    else:
                        break
                return num_args

            # set up the proxy inputs to bw_module
            # the calling convention is: [*symints, *args (primals and tangents), backward_state]
            num_args = num_inputs(bw_module.graph)  # type: ignore[attr-defined]
            pall_args = [
                pgrads[i] for i in range(num_args - int(pbackward_state is not None))
            ]
            # replace the symints with our symints
            symints = ctx._get_compiled_autograd_symints()
            assert len(symints) == len(ctx.symints)
            psymints = [self.to_proxy(e) for e in symints]
            pall_args[: len(symints)] = psymints
            # Add backward_state
            if pbackward_state is not None:
                pall_args.append(pbackward_state)

            # run over all nodes of the aot_backward graph.
            # copy and paste them all into the compiled autograd graph.
            args_idx = 0
            # pyrefly: ignore [implicit-any]
            value_remap = {}
            poutputs: list[torch.fx.Proxy] | None = None

            # names of nodes must appear only once in the fx.Graph
            # dedup AOT backwards that appear multiple times
            deduped_aot_id = str(aot_id)
            if self.aot_id_counter[aot_id]:
                deduped_aot_id += f"_{self.aot_id_counter[aot_id]}"
            self.aot_id_counter[aot_id] += 1

            def make_unique(node_name: str) -> str:
                # make it both informative and unique
                return f"aot{deduped_aot_id}_{node_name}"

            for node in bw_module.graph.nodes:  # type: ignore[attr-defined]
                if node.op == "placeholder":
                    ph = pall_args[args_idx].node
                    ph.name = make_unique(node.name)
                    value_remap[node] = ph
                    args_idx += 1
                elif node.op == "output":
                    assert len(node.args) == 1
                    poutputs = [
                        torch.fx.Proxy(value_remap[n], self.fx_tracer)
                        if isinstance(n, torch.fx.Node)
                        else n
                        for n in node.args[0]
                    ]
                elif node.op == "get_attr":
                    name = node.target
                    qualname = self.fx_tracer.get_fresh_qualname(name)
                    setattr(self.fx_tracer.root, qualname, getattr(bw_module, name))
                    result = self.fx_tracer.create_node("get_attr", qualname, (), {})
                    result.name = make_unique(node.name)
                    value_remap[node] = result
                elif node.op == "call_function":
                    if node.target is torch.ops.aten.view.default:
                        # this aot bwd graph is being lazily compiled
                        # we must manually apply the view_to_reshape post grad pass
                        # since it was already applied to the aot fwd, and baked into the gradients
                        node.target = torch.ops.aten.reshape.default
                    result = self.fx_tracer.graph.node_copy(
                        node, lambda n: value_remap[n]
                    )
                    result.name = make_unique(node.name)
                    value_remap[node] = result
                elif node.op == "call_module":
                    name = node.target
                    qualname = self.fx_tracer.get_fresh_qualname(name)
                    setattr(self.fx_tracer.root, qualname, getattr(bw_module, name))
                    result = self.fx_tracer.graph.node_copy(
                        node, lambda n: value_remap[n]
                    )
                    result.target = qualname
                    value_remap[node] = result
                else:
                    raise AssertionError("shouldn't get here")

            assert poutputs is not None

            # In general we don't know what the shapes of the outputs are, so allocate
            # some dummy sizes for them.
            def dummy() -> torch.Tensor:
                with disable_proxy_modes_tracing():
                    return torch.zeros(0, 0, 0, 0, 123)

            outputs = [
                dummy() if isinstance(o, torch.fx.Proxy) else o for o in poutputs
            ]
            self.bind_objects_to_proxies(outputs, poutputs)
            return outputs