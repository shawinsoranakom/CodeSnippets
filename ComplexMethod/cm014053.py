def make_call_generated_code(self, fn_name: str) -> None:
        """Call the generated code function stored in fn_name"""
        self.extend_output(self.load_function_name(fn_name, True))

        graphargs = self.tx.output.graphargs

        def extract_nested_sources(source: Source) -> list[Source]:
            nested_sources: list[Source] = []
            if isinstance(source, ChainedSource):
                nested_sources.append(source.base)
            if isinstance(source, DictGetItemSource) and isinstance(
                source.index, Source
            ):
                nested_sources.append(source.index)
            return nested_sources

        def collect_temp_sources(sources: deque[Source], codegen: PyCodegen) -> None:
            seen_sources: OrderedSet[Source] = OrderedSet()
            while sources:
                current_source = sources.popleft()
                if current_source in seen_sources:
                    # This source is used at least twice, so it can be reused
                    codegen.mark_source_temp(current_source)
                    # Dont trace source further. This prevents us from marking too
                    # many nodes as temp sources.
                    continue
                seen_sources.add(current_source)
                sources.extend(extract_nested_sources(current_source))

        # Collect all the sources that are used more than once, so that we can
        # generate tmp variables in the generated pre-graph bytecode. This
        # essentially implements CSE.
        collect_temp_sources(
            deque([arg.source for arg in graphargs if arg.source is not None]), self
        )

        cm_var = None
        if config.record_runtime_overhead:
            # Record the pregraph bytecode start
            self.add_push_null(
                lambda: self.load_import_from(
                    utils.__name__, "record_pregraph_bytecode_enter"
                )
            )
            self.extend_output(create_call_function(0, False))
            cm_var = self.new_var()
            self.store(cm_var)

        for arg in graphargs:
            if arg.pass_arg_as_tensor:
                self.add_push_null(
                    lambda: self.extend_output(
                        [
                            self.create_load_python_module(torch),
                            self.create_load_attr("_as_tensor_fullprec"),
                        ]
                    )
                )
                self.call_reconstruct(arg)
                self.extend_output(create_call_function(1, False))
            else:
                self.call_reconstruct(arg)

        if config.record_runtime_overhead:
            # Record the pregraph bytecode end
            self.add_push_null(
                lambda: self.load_import_from(
                    utils.__name__, "record_pregraph_bytecode_exit"
                )
            )
            assert cm_var is not None
            self.extend_output([self.create_load(cm_var)])
            self.extend_output(create_call_function(1, False))
            self.pop_top()

        self.extend_output(create_call_function(len(graphargs), False))