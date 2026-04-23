def bytecode_hook(code, out_code):
            import dis
            import sys

            nonlocal match_done

            # test is sensitive to what Dynamo traces. So as soon as the main
            # graph is tested, we skip the bytecode hook checks for future
            # frames.
            if not match_done:
                if sys.version_info < (3, 11):
                    call_op = "CALL_FUNCTION"
                else:
                    call_op = "CALL"

                insts = list(dis.get_instructions(out_code))
                # Find the CALL that invokes the compiled graph function
                # (not an earlier CALL from e.g. store_user_object_weakrefs).
                load_graph_idx = next(
                    i
                    for i, inst in enumerate(insts)
                    if inst.opname == "LOAD_GLOBAL"
                    and isinstance(inst.argval, str)
                    and inst.argval.startswith("__compiled_fn")
                )
                call_graph_idx = next(
                    i
                    for i, inst in enumerate(insts)
                    if i > load_graph_idx and inst.opname == call_op
                )
                # pre-graph should alias: inputs_ref_0 = inputs[0]
                matches = [
                    inst
                    for inst in insts[:call_graph_idx]
                    if inst.opname == "STORE_FAST" and inst.argval == "inputs_ref_0"
                ]
                self.assertTrue(len(matches) == 1)
                # post-graph should access inputs_ref_0 instead of inputs
                matches = [
                    inst for inst in insts[call_graph_idx:] if inst.argval == "inputs"
                ]
                self.assertTrue(len(matches) == 0)
                matches = [
                    inst
                    for inst in insts[call_graph_idx:]
                    if inst.opname == "LOAD_FAST" and inst.argval == "inputs_ref_0"
                ]
                self.assertTrue(len(matches) == 1)
                match_done = True