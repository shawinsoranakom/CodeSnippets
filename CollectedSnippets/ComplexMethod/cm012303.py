def __call__(self, graph: fx.Graph) -> None:
        target_devices = OrderedSet[torch.device]()
        constructors = []
        cpu_placeholders: OrderedSet[fx.Node] = OrderedSet()

        for node in graph.nodes:
            device = self.get_node_device(node)
            if device and device.type == self.target:
                target_devices.add(device)

            if (
                self.allow_inputs
                and node.op == "placeholder"
                and self.is_cpu_scalar_tensor(node)
            ):
                cpu_placeholders.add(node)
                constructors.append(node)
                continue

            if not (
                isinstance(node.target, torch._ops.OpOverload)
                and node.target.namespace in ("prims", "aten")
            ):
                continue

            if not torch._subclasses.fake_tensor._is_tensor_constructor(node.target):
                continue

            if node.kwargs.get("device") != torch.device("cpu"):
                continue

            constructors.append(node)

        # not handling multiple target devices initially
        if not constructors or len(target_devices) != 1:
            return

        movable_constructors = self.find_movable_constructors(graph, constructors)

        target_device = next(iter(target_devices))
        movable_cpu_placeholders = movable_constructors & cpu_placeholders
        if movable_cpu_placeholders:
            node = next(iter(reversed(movable_cpu_placeholders)))
            last_node = node
            unsqueezed_nodes = []
            for elem in movable_cpu_placeholders:
                with graph.inserting_after(last_node):
                    unsqueezed_nodes.append(
                        graph.call_function(torch.ops.aten.unsqueeze.default, (elem, 0))
                    )
                    last_node = unsqueezed_nodes[-1]
            with graph.inserting_after(last_node):
                cpu_concat = graph.call_function(
                    torch.ops.aten.cat.default, (unsqueezed_nodes,)
                )
                last_node = cpu_concat
            with graph.inserting_after(last_node):
                gpu_concat = graph.call_function(
                    torch.ops.prims.device_put.default,
                    (cpu_concat, target_device, True),
                )
                last_node = gpu_concat
            with graph.inserting_after(last_node):
                gpu_split = graph.call_function(
                    torch.ops.aten.unbind.int, (gpu_concat,)
                )
                last_node = gpu_split
            for idx, node in enumerate(movable_cpu_placeholders):
                with graph.inserting_after(last_node):
                    gpu_node = graph.call_function(operator.getitem, (gpu_split, idx))
                    node.replace_all_uses_with(
                        gpu_node,
                        lambda x: x
                        not in [cpu_concat, gpu_concat, gpu_split, gpu_node]
                        + unsqueezed_nodes
                        and x.target != torch.ops.aten.copy_.default
                        and x.target != "output",
                    )
                    last_node = gpu_node

                # noop elimination if there are other device_put for gpu_node to
                # target device. Alternatively, we could just move the other device_put
                # earlier in the graph, but that is not supported in fx graph yet.
                noop_device_puts = [
                    user
                    for user in gpu_node.users
                    if user.target is torch.ops.prims.device_put.default
                    and user.args[1] == target_device
                ]
                for noop in noop_device_puts:
                    noop.replace_all_uses_with(gpu_node)
                    graph.erase_node(noop)

        movable_constructors -= movable_cpu_placeholders
        for node in movable_constructors:
            kwargs = node.kwargs.copy()
            kwargs["device"] = target_device
            node.kwargs = kwargs