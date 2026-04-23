def analyze_potential_input_alias_or_mutation(name, aliases, input_mutations):
    if any(len(a) > 0 for a in aliases):
        # TODO: Investigate here further which node is exactly aliasing
        raise RuntimeError(
            f"{name} where aliases appear. "
            + f"In particular, these inputs \
            {set(el for el_map in aliases if len(el_map.keys()) > 0 for el in el_map)} "  # noqa: C401
            + "get aliased. Please ensure that this doesn't happen."
        )
    if len(input_mutations):
        # TODO: Investigate here further which node is exactly mutating the inputs
        raise RuntimeError(
            f"{name} where the inputs are mutated. "
            + f"In particular, these nodes are mutating the inputs \
            {set(el for el in input_mutations)}."  # noqa: C401
            + "Please ensure that this doesn't happen."
        )