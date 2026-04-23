def memory_plan_reuse_patched(self):
    import torch._inductor.ir as ir
    from torch._inductor.codegen.wrapper import (
        EnterSubgraphLine,
        ExitSubgraphLine,
        MemoryPlanningLine,
        MemoryPlanningState,
        SubgraphPythonWrapperCodegen,
    )
    from torch._inductor.virtualized import V

    def get_output_names(graph_outputs) -> list[str]:
        import itertools

        names = []
        shape_counter = itertools.count(0)
        none_counter = itertools.count(0)
        for node in graph_outputs:
            if isinstance(node, ir.NoneAsConstantBuffer):
                names.append(f"{V.graph.name}_none{next(none_counter)}")
            elif isinstance(node, ir.ShapeAsConstantBuffer):
                names.append(f"{V.graph.name}_shape{next(shape_counter)}")
            else:
                names.append(node.get_name())
        return names

    if (
        isinstance(V.graph.wrapper_code, SubgraphPythonWrapperCodegen)
        and V.graph.wrapper_code.partition_signatures is not None
    ):
        out_names = get_output_names(
            V.graph.wrapper_code.partition_signatures.output_nodes
        )
    else:
        out_names = V.graph.get_output_names()

    while (
        self.lines
        and isinstance(self.lines[-1], MemoryPlanningLine)
        and self.lines[-1].node.name not in out_names  # type: ignore[attr-defined]
    ):
        # these lines will be pointless
        self.lines.pop()

    # codegen allocations in two passes
    planning_states = [MemoryPlanningState()]
    past_planning_states = []
    for i in range(len(self.lines)):
        line = self.lines[i]
        if isinstance(line, MemoryPlanningLine):
            self.lines[i] = line.plan(planning_states[-1])
        elif isinstance(line, EnterSubgraphLine):
            planning_states.append(MemoryPlanningState())
        elif isinstance(line, ExitSubgraphLine):
            past_planning_states.append(planning_states.pop())
    past_planning_states.append(planning_states.pop())
    assert len(planning_states) == 0