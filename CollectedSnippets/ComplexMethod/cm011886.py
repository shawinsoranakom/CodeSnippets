def check_fn(match: Match) -> bool:
        """
        Often shapes get burned into the pattern, so our initial match ran with
        `ignore_types=(int, ...)`.

        Recheck the match with the correct shapes.
        """
        argnames = list(argnames_static)
        for name in argnames:
            if name not in match.kwargs:
                raise RuntimeError(
                    f"Not all inputs to pattern found in match.kwargs. Perhaps one "
                    f"of the inputs is unused? argnames={argnames}, match.kwargs={match.kwargs}"
                )

        args = list(
            torch.fx.map_arg(
                [match.kwargs[name] for name in argnames], lambda n: n.meta["val"]
            )
        )

        sym_args: list[torch.SymInt] = []
        fake_mode = torch._dynamo.utils.detect_fake_mode(args)
        assert fake_mode is not None
        with fake_mode:
            for i, grad in enumerate(requires_grad):
                if isinstance(args[i], torch.Tensor):
                    # pyrefly: ignore [missing-attribute]
                    if grad and is_integer_dtype(args[i].dtype):
                        return False

                    args[i] = torch.empty_strided(
                        # pyrefly: ignore [missing-attribute]
                        args[i].size(),
                        # pyrefly: ignore [missing-attribute]
                        args[i].stride(),
                        # pyrefly: ignore [missing-attribute]
                        dtype=args[i].dtype,
                        # pyrefly: ignore [missing-attribute]
                        device=args[i].device,
                        requires_grad=grad,
                    )
                    # pyrefly: ignore [missing-attribute]
                    for v in itertools.chain(args[i].shape, args[i].stride()):
                        if isinstance(v, torch.SymInt) and all(
                            statically_known_true(v != a) for a in sym_args
                        ):
                            sym_args.append(v)

            # If we were given a pre-traced pattern then use that instead of
            # retracing. Note that this means the pattern has to be independent
            # of its args.
            specific_pattern = search_fn_pattern

            if not specific_pattern:
                if sym_args:
                    # AOT Autograd and make fx will dedupe symbolic shape size
                    # accesses of sym ints that appear as inputs
                    # We don't want the sym_size uses to interfere with pattern matching
                    # so we provide them as inputs.
                    # Later, when we actually do the replacement, the symbolic shape
                    # sizes will get re-traced and added to the graph.

                    def search_fn_new(*args_new: Any, **_: Any) -> Any:
                        return search_fn(*args_new[len(args_new) - len(args) :])

                    try:
                        specific_graph = trace_fn(
                            search_fn_new,
                            sym_args + args,
                            get_decomp_fn=get_decomp_fn,
                        )
                    except RuntimeError as e:
                        log_trace_failure(search_fn, e)
                        return False

                    # correct argnames in the graph
                    sym_arg_names = []
                    for i, placeholder in zip(
                        range(len(sym_args) + len(args)),
                        specific_graph.graph.nodes,
                    ):
                        if i < len(sym_args):
                            sym_arg_names.append(placeholder.target)
                            continue

                        with specific_graph.graph.inserting_after(placeholder):
                            new_node = specific_graph.graph.placeholder(
                                argnames[i - len(sym_args)]
                            )
                            new_node.target = new_node.name
                            placeholder.replace_all_uses_with(new_node)
                            specific_graph.graph.erase_node(placeholder)

                    argnames = sym_arg_names + argnames
                else:
                    try:
                        specific_graph = trace_fn(
                            search_fn, args, get_decomp_fn=get_decomp_fn
                        )
                    except RuntimeError as e:
                        log_trace_failure(search_fn, e)
                        return False

                specific_pattern = fx_to_pattern(
                    specific_graph,
                    argnames=argnames,
                    exclusive_arg_names=exclusive_arg_names,
                    scalar_workaround=scalar_workaround,
                )

            node = match.output_nodes()[0]
            assert node is not None
            specific_pattern_match = specific_pattern.match(node)

            if _should_debug_node(node.name):
                log.warning(
                    "Specific pattern match: %s%s %s %s",
                    node,
                    node.args,
                    specific_pattern_match,
                    specific_pattern,
                )

            if is_match(specific_pattern_match) and extra_check(specific_pattern_match):
                # trace the pattern using the shapes from the user program
                match.replacement_graph = trace_fn(
                    replace_fn, args, get_decomp_fn=get_decomp_fn
                )
                if len(match.nodes) == 1:
                    for n in match.replacement_graph.graph.nodes:
                        _transfer_meta(
                            new_meta=n.meta,
                            old_node=match.nodes[0],
                            pass_name="replacement",
                        )
                return True
            return False