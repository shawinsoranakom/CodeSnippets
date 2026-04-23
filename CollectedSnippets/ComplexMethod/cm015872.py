def _test_wrapper_codegen_statically_known_int_or_none_in_context():
            nonlocal call_count
            call_count += 1
            graph = V.graph
            input_layouts = [
                inp.layout
                for inp in graph.graph_inputs.values()
                if hasattr(inp, "layout")
            ]
            batch_dim = input_layouts[0].size[0]
            if call_count == 1:
                # testing fn_1
                if (
                    PythonWrapperCodegen.statically_known_int_or_none(batch_dim)
                    is not None
                ):
                    raise AssertionError("Should not be statically known on first call")
            elif call_count == 2:
                # testing fn_2
                if PythonWrapperCodegen.statically_known_int_or_none(batch_dim) != 5:
                    raise AssertionError(
                        "Should be limited to exactly 5 on second call due to multiple constraints"
                    )
            elif call_count == 2:
                # testing fn_3
                if PythonWrapperCodegen.statically_known_int_or_none(batch_dim) != 5:
                    raise AssertionError("Should be exactly 5 on third call")