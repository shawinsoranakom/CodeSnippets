def _extract_fake_inputs(gm, args, kwargs):
    """
    Given a graph module, extract fakified input tensors from the metadata of
    its placeholders, and map them to the structure of given args and kwargs.
    Also return the fake mode used to fakify those inputs.
    """
    fake_inps: list[Any] = []
    fake_vals: list[Any] = []
    for node in gm.graph.nodes:
        if node.op == "placeholder":
            fake_inps.append(node.meta.get("val"))
        else:
            fake_vals.append(node.meta.get("example_value"))

    if dynamo_bytecode_flatten := getattr(gm, "_dynamo_bytecode_flatten", None):
        # In _extract_fake_inputs, the goal is to make real inputs into
        # fake (and symbolic) inputs. The way currently it's implemented
        # is by looking at the node.meta["val"] of the placeholder nodes.
        # This doesn't work when the graph is Dynamo flattened, because now
        # plceholder nodes doesn't have the ordering like pytree inputs do.
        # Instead, we need to look at how the inputs are shuffled, and map
        # the inputs to their actual fake inputs and symbolic inputs.
        # Since inputs can also contain symints, we cannot simply use the
        # FakeTensorMode memo to look up tensors only there.

        fake_inps = []
        positions = {}
        idx = 0

        def mark_inputs(x):
            # x can be a tensor or symbolic integer or a normal constant.
            nonlocal idx
            fake_inps.append(x)
            if isinstance(x, torch.Tensor):
                ret = x
            else:
                ret = object()
            if id(ret) not in positions:
                positions[id(ret)] = idx
            idx += 1
            return ret

        dummy_args = pytree.tree_map(mark_inputs, args + tuple(kwargs.values()))
        shuffled_args = dynamo_bytecode_flatten(*dummy_args)

        for node, shuffled_arg in zip(
            gm.graph.find_nodes(op="placeholder"), shuffled_args
        ):
            if id(shuffled_arg) in positions:
                fake_inps[positions[id(shuffled_arg)]] = node.meta.get("val")

    # We get both because now we might have a combination of symint and tensor
    # inputs, and we want to check that the shape env is consistent between
    # both. Unfortunately we can't see what fake mode is attached to the shape
    # env, then we can just compare fake modes.
    detected_fake_mode = detect_fake_mode(fake_inps + fake_vals)
    detected_shape_env = detect_shape_env(fake_inps + fake_vals)

    if detected_fake_mode:
        if detected_shape_env:
            if detected_shape_env is not detected_fake_mode.shape_env:
                raise AssertionError(
                    "Detected shape env does not match fake mode's shape env"
                )
        fake_mode = detected_fake_mode
    elif detected_shape_env:
        fake_mode = FakeTensorMode(shape_env=detected_shape_env, export=True)
    else:
        fake_mode = FakeTensorMode(shape_env=ShapeEnv(), export=True)

    count = 0

    def lookup_fake(x):
        nonlocal count
        val = fake_inps[count] if isinstance(x, (int, torch.Tensor)) else x
        count += 1
        return val

    fake_args = pytree.tree_map(lookup_fake, args)
    fake_kwargs = pytree.tree_map(lookup_fake, kwargs)

    return fake_args, fake_kwargs, fake_mode