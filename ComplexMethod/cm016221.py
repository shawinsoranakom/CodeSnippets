def convert_graph_to_python_code(
    operation_graph: OperationGraph,
    seed: int | None = None,
    template: str = "default",
) -> str:
    """
    Convert an operation graph to executable Python code using topological ordering.

    The graph-based approach generates code by:
    1. Getting the topological order of nodes (dependencies before dependents)
    2. Generating code for each node in that order
    3. Properly handling input dependencies through node connections

    Args:
        operation_graph: OperationGraph instance containing the operation DAG
        seed: Random seed for reproducible code generation. If None, uses current random state.

    Returns:
        String containing the complete Python code that executes the operations
    """

    # Instantiate template
    if template == "dtensor":
        fuzz_template = DTensorFuzzTemplate()
    elif template == "dtensor_placements":
        fuzz_template = DTensorFuzzPlacementsTemplate()
    elif template == "unbacked":
        fuzz_template = UnbackedFuzzTemplate()
    elif template == "streams":
        fuzz_template = StreamFuzzTemplate()
    else:
        fuzz_template = DefaultFuzzTemplate()

    # Set seed for reproducible code generation
    if seed is not None:
        import random

        random.seed(seed + 1000)  # Offset to avoid conflicts with graph generation
        torch.manual_seed(seed + 1000)

    if not operation_graph.nodes:
        raise ValueError("Empty operation graph")

    # Get topological order - this ensures dependencies are processed before dependents
    topo_order = operation_graph.get_topological_order()

    # Track generated variables, arg operations, and constant operations
    generated_code_lines = []
    node_variables: dict[str, tuple[str, Spec]] = {}  # Maps node_id to (var_name, spec)
    arg_operations: list[
        tuple[str, Spec]
    ] = []  # List of (node_id, spec) for arg operations
    constant_operations: list[
        tuple[str, str, Spec]
    ] = []  # List of (node_id, var_name, spec) for constant operations (DTensor templates only)

    # Process nodes in topological order
    for node_id in topo_order:
        node = operation_graph.nodes[node_id]
        op_name = node.op_name
        output_spec = node.output_spec

        # Generate output variable name
        output_var_name = f"var_{node_id}"

        # Generate input variable names from input nodes
        input_var_names = []
        for input_node_id in node.input_nodes:
            if input_node_id in node_variables:
                input_var_name, _ = node_variables[input_node_id]
                input_var_names.append(input_var_name)
            else:
                raise ValueError(
                    f"Node {node_id} depends on {input_node_id}, but {input_node_id} "
                    f"was not processed yet. Topological order may be incorrect."
                )

        # Handle different operation types
        if op_name == "arg" or op_name.startswith("arg_"):
            # Track arg operations for later function signature generation
            arg_operations.append((node_id, output_spec))
            arg_name = f"arg_{len(arg_operations) - 1}"
            # Add tensor descriptor comment for arg operations too
            descriptor_comment = f"# {format_tensor_descriptor(output_spec)}"
            operation_lines = [f"{output_var_name} = {arg_name} " + descriptor_comment]
        elif op_name == "constant" and template == "dtensor_placements":
            # For DTensor placements template, track constants to create them outside the function
            constant_operations.append((node_id, output_var_name, output_spec))
            descriptor_comment = f"# {format_tensor_descriptor(output_spec)}"
            operation_lines = [
                f"{output_var_name} = {output_var_name} " + descriptor_comment
            ]
        else:
            # Generate operation execution code
            operation_lines = generate_simple_operation_code(
                output_var_name, input_var_names, op_name, output_spec
            )

        # Add proper indentation for function body
        generated_code_lines.extend(["    " + line for line in operation_lines])

        # Track this node's variable
        node_variables[node_id] = (output_var_name, output_spec)

    # Wrap body with stream contexts if using the streams template
    if template == "streams":
        generated_code_lines = StreamFuzzTemplate.wrap_body_with_streams(
            generated_code_lines, operation_graph
        )

    # The final result comes from the root node
    root_node_id = operation_graph.root_node_id
    if root_node_id not in node_variables:
        raise ValueError(f"Root node {root_node_id} was not processed")

    final_var_name, _ = node_variables[root_node_id]

    # Generate function signature based on discovered arg and constant operations
    param_names = []
    if arg_operations:
        param_names.extend([f"arg_{i}" for i in range(len(arg_operations))])
    if template == "dtensor_placements" and constant_operations:
        param_names.extend([var_name for _, var_name, _ in constant_operations])
    param_names.append("sentinel")

    function_signature = f"def fuzzed_program({', '.join(param_names)})"

    # Build the complete code - all imports at the top
    code_lines = []

    # Add template imports
    code_lines.extend(fuzz_template.imports_codegen())

    # Add template flags
    code_lines.extend(fuzz_template.flags_codegen())
    code_lines.append("")

    # Add single seed at the top if seed is provided
    if seed is not None:
        code_lines.append(f"torch.manual_seed({seed})")
        code_lines.append("")

    code_lines.append(function_signature + ":")

    # Add the generated operation code
    code_lines.extend(generated_code_lines)

    # Add return statement with sentinel multiplication to ensure gradient computation
    # Handle complex tensors appropriately based on template
    if template in ["dtensor", "dtensor_placements"]:
        # For DTensor, avoid .real operation which doesn't work with sharding
        # Instead use abs() for complex tensors to get a real result
        code_lines.extend(
            [
                "    # Ensure gradient computation by multiplying with sentinel",
                f"    result = {final_var_name} * sentinel",
                "    if result.is_complex():",
                "        result = result.abs()  # Use abs() instead of .real for DTensor compatibility",
                "    return result",
                "",
            ]
        )
    else:
        code_lines.extend(
            [
                "    # Ensure gradient computation by multiplying with sentinel and taking real part",
                f"    result = {final_var_name} * sentinel",
                "    if result.is_complex():",
                "        result = result.real",
                "    return result",
                "",
            ]
        )

    # Generate argument creation code using template
    if template == "dtensor_placements" and hasattr(fuzz_template, "args_codegen"):
        # For dtensor_placements, pass constants to args_codegen which handles both
        arg_code_lines = fuzz_template.args_codegen(arg_operations, constant_operations)
        code_lines.extend(arg_code_lines)
    else:
        arg_code_lines = fuzz_template.args_codegen(arg_operations)
        code_lines.extend(arg_code_lines)

    # Generate the final execution with both normal and compiled versions
    param_values = []
    if arg_operations:
        param_values.extend([f"arg_{i}" for i in range(len(arg_operations))])
    if template == "dtensor_placements" and constant_operations:
        param_values.extend([var_name for _, var_name, _ in constant_operations])
    param_values.append("sentinel")

    if len(param_values) == 1:
        args_tuple = (
            f"({param_values[0]},)"  # Single element tuple needs trailing comma
        )
    else:
        args_tuple = f"({', '.join(param_values)})"

    # Generate execution code using template check
    check_lines = fuzz_template.check.codegen(args_tuple)
    code_lines.extend([""] + check_lines)

    # Add template epilogue
    epilogue_lines = fuzz_template.epilogue_codegen()
    if epilogue_lines:
        code_lines.append("")
        code_lines.extend(epilogue_lines)

    return "\n".join(code_lines)