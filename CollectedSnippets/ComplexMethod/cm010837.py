def _check_if_mutation_can_be_in_graph(
    keep_input_mutations: bool,
    mutates_data: bool,
    mutates_metadata: bool,
    mutations_hidden_from_autograd: bool,
    mutations_under_no_grad_or_inference_mode: bool,
    mutates_storage_metadata: bool,
    mutation_inductor_storage_resize: bool,
    requires_grad: bool,
) -> bool:
    if keep_input_mutations:
        in_graph = (
            mutates_data or mutates_storage_metadata or mutation_inductor_storage_resize
        ) and (
            (not mutates_metadata and not requires_grad)
            or mutations_hidden_from_autograd
            or mutations_under_no_grad_or_inference_mode
        )
    else:
        in_graph = False
    # See Note [set_() Input Mutations in AOTAutograd]
    # If there was a `set_()`, we require that all mutations were under no_grad,
    # so we can (safely) emit the set_() in the graph at runtime
    # resize_() gets the same treatment
    if mutation_inductor_storage_resize or mutates_storage_metadata:
        op_name = "resize_" if mutation_inductor_storage_resize else "set_"
        if not in_graph:
            raise AssertionError(f"""\
Encountered a {op_name} on a graph input, but the input has other mutations that we cannot
keep in the graph. This is not supported today. Current state:
  keep_input_mutations={keep_input_mutations}
  mutates_data={mutates_data}
  mutates_metadata={mutates_metadata}
  mutations_hidden_from_autograd={mutations_hidden_from_autograd}
  mutations_under_no_grad_or_inference_mode={mutations_under_no_grad_or_inference_mode}
  mutation_inductor_storage_resize={mutation_inductor_storage_resize}
  requires_grad={requires_grad}""")
    return in_graph