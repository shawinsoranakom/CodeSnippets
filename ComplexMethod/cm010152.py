def _verify_exported_program_module_call_graph(exported_program) -> None:
    module_call_graph = exported_program.module_call_graph
    nodes = {node.name for node in exported_program.graph.nodes}
    for entry in module_call_graph:
        if entry.signature is not None:
            for arg in entry.signature.inputs:
                if arg.name and arg.name not in nodes:
                    raise SpecViolationError(
                        f"Input {arg.name} does not exist in the graph."
                    )
            for arg in entry.signature.outputs:
                if arg.name and arg.name not in nodes:
                    raise SpecViolationError(
                        f"Output {arg.name} does not exist in the graph."
                    )