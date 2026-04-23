def lower_to_elementwise_interpreter(
            orig_mod: torch.nn.Module,
        ) -> torch.nn.Module:
            # ===== Stage 1: Symbolic trace the module =====
            mod = symbolic_trace(orig_mod)

            # ===== Stage 2: Lower GraphModule representation to the C++
            #       interpreter's instruction format ======
            instructions = []
            constant_idx = 0
            constants = {}
            fn_input_names = []

            target_to_name = {operator.add: "add", operator.mul: "mul"}

            output_node: Node | None = None
            # For each instruction, create a triple
            # (instruction_name : str, inputs : List[str], output : str)
            # to feed into the C++ interpreter
            for n in mod.graph.nodes:
                target, args, out_name = n.target, n.args, n.name
                if len(n.kwargs) != 0:
                    raise AssertionError("kwargs currently not supported")

                if n.op == "placeholder":
                    # Placeholders specify function argument names. Save these
                    # for later when we generate the wrapper GraphModule
                    fn_input_names.append(target)
                elif n.op == "call_function":
                    if target not in target_to_name:
                        raise AssertionError("Unsupported call target " + str(target))
                    arg_names = []
                    for arg in args:
                        if not isinstance(arg, Node):
                            # Pull out constants. These constants will later be
                            # fed to the interpreter C++ object via add_constant()
                            arg_name = f"constant_{constant_idx}"
                            constants[arg_name] = torch.tensor(
                                [arg] if isinstance(arg, numbers.Number) else arg
                            )
                            arg_names.append(arg_name)
                            constant_idx += 1
                        else:
                            arg_names.append(arg.name)
                    instructions.append((target_to_name[target], arg_names, out_name))
                elif n.op == "output":
                    if output_node is not None:
                        raise RuntimeError("Multiple output nodes!")
                    output_node = n
                else:
                    raise RuntimeError("Unsupported opcode " + n.op)

            interpreter = torch.classes._TorchScriptTesting._ElementwiseInterpreter()
            # Load constants
            for k, v in constants.items():
                interpreter.add_constant(k, v)
            # Specify names for positional input arguments
            interpreter.set_input_names(fn_input_names)
            # Load instructions
            interpreter.set_instructions(instructions)
            # Specify name for single output
            if not isinstance(output_node.args[0], torch.fx.Node):
                raise AssertionError(
                    f"Expected output_node.args[0] to be torch.fx.Node, "
                    f"got {type(output_node.args[0])}"
                )
            interpreter.set_output_name(output_node.args[0].name)

            # ===== Stage 3: Create a wrapper GraphModule around the interpreter =====
            class WrapperModule(torch.nn.Module):
                def __init__(self, interpreter):
                    super().__init__()
                    self.interpreter = interpreter

            wrapper = WrapperModule(interpreter)

            # Create a graph that: 1) Takes function arguments 2) Invokes the interpreter
            # 3) Returns the specified return value

            # FIXME: The following code could be greatly simplified by symbolic_trace'ing
            # the wrapper with a Tracer that considers the Wrapper instance a root
            # module, however, I can't get `__call__` exposed on TorchBind classes
            # without it messing up Python `hasattr` for some reason. More digging
            # into CPython's implementation of hasattr is probably in order...

            graph = torch.fx.Graph()
            # Add placeholders for fn inputs
            placeholder_nodes = []
            for name in fn_input_names:
                placeholder_nodes.append(graph.create_node("placeholder", name))

            # Get the interpreter object
            interpreter_node = graph.create_node("get_attr", "interpreter")

            # Add a node to call the interpreter instance
            output_node = graph.create_node(
                op="call_method",
                target="__call__",
                args=(interpreter_node, placeholder_nodes),
            )

            # Register output
            graph.output(output_node)

            graph.lint()

            # Return final GraphModule!!!
            return GraphModule(wrapper, graph)