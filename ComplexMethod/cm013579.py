def record_cross_partition_use(def_node: Node, use_node: Node | None) -> None:
        from torch.fx.experimental.symbolic_shapes import free_symbols

        defined = getattr(def_node, "_fx_partition", None)
        used = getattr(use_node, "_fx_partition", None)

        log.debug(
            "record_cross_partition_use %s (%s) %s (%s)",
            def_node.name,
            defined,
            use_node.name if use_node is not None else "-",
            used,
        )

        if defined != used:
            if defined is not None:
                def_partition = partitions[defined]
                def_partition.outputs.setdefault(def_node.name)
                if used is not None:
                    def_partition.dependents.setdefault(used)

            if used is not None:
                use_partition = partitions[used]
                use_partition.inputs.setdefault(def_node.name)
                # We have made def_node an input to the use_partition.  If
                # this input has symbolic symbols in its size, those also must
                # be made as inputs to the partition
                if (def_val := def_node.meta.get("example_value")) is not None:
                    for s in sorted(free_symbols(def_val), key=str):
                        s_node = symbol_to_node[s]
                        use_partition.inputs.setdefault(s_node.name)
                        if symbol_to_node[s].op != "placeholder":
                            # If the node that defines the symbol is not a
                            # placeholder, we must make it an output of the
                            # partition.  Note that this may be in a different
                            # partition than defined!  Although, this doesn't
                            # really make a difference for correctness, since
                            # defined is guaranteed to have the symbol in
                            # scope and can return it; you just get less
                            # optimal codegen in this case.
                            s_defined = getattr(s_node, "_fx_partition", None)
                            if s_defined is not None:
                                s_def_partition = partitions[s_defined]
                                s_def_partition.outputs.setdefault(s_node.name)
                                s_def_partition.dependents.setdefault(used)
                                use_partition.dependencies.setdefault(s_defined)
                if defined is not None:
                    use_partition.dependencies.setdefault(defined)