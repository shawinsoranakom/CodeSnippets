def _setup_prologue_hook(self, input_name, prologue_sources=None):
        ir_node = self._template_buffer._named_inputs.get(input_name)
        if ir_node is None:
            return
        self.named_input_nodes[input_name] = ir_node
        input_buf = ir_node.get_name()
        source_bufs = (
            prologue_sources.get(input_buf) if prologue_sources is not None else None
        )
        if source_bufs is None:
            return
        source_buffer = next(iter(source_bufs)) if source_bufs else None
        self._prologue_source_buffers[input_name] = source_buffer
        if source_buffer is not None:
            self.args.input_buffers[source_buffer] = input_name
        for src in source_bufs:
            if src != source_buffer:
                if src not in self._extra_inputs:
                    self._extra_inputs[src] = f"_extra_input_{len(self._extra_inputs)}"
                self.args.input_buffers[src] = self._extra_inputs[src]

        subgraph_name = f"<LOAD_INPUT_{input_name}>"
        result_var = f"_prologue_{input_name}_result"

        # Compute prologue variable names once and store them.
        renames = {
            "xindex": f"_prologue_{input_name}_xindex",
            "xmask": f"_prologue_{input_name}_xmask",
        }
        self._prologue_vars[input_name] = {
            "xindex": renames["xindex"],
            "xmask": renames["xmask"],
            "result": result_var,
        }

        class _CaptureStoreHandler(V.WrapperHandler):  # type: ignore[name-defined]
            def store(self, name, index, value, mode=None):
                V.kernel.store_buffer_names.add(name)
                V.kernel.cse.store_cache[name] = value
                V.kernel.compute.writeline(f"{result_var} = {value}")

        self._make_independent_subgraph(
            subgraph_name,
            sympy_product(ir_node.get_size()),
            ops_handler=_CaptureStoreHandler,
            root_var_renames=renames,
        )

        def hook(_name=subgraph_name, _input=input_name, _self=self):
            with _self.set_subgraph_body(_name):
                _self.codegen_body()
                _self.cse.invalidate(OrderedSet())
                body = _self.body.getvalue()
            # Rename range-tree root variables (xindex/xmask) to avoid collisions
            # across prologue subgraphs.  tmp/x0 names are already unique (shared
            # kernel-level counters).  Read renames from the subgraph info.
            subgraph = _self.subgraph_bodies[_name]
            for orig, renamed in subgraph.root_var_renames.items():
                body = re.sub(rf"\b{orig}\b", renamed, body)
            return body.rstrip()

        self.render_hooks[f"<LOAD_INPUT_{input_name}>"] = hook