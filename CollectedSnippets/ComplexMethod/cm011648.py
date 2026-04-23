def get_kernel_metadata(
    node_schedule: Sequence[BaseSchedulerNode] | ExternKernel,
    wrapper: PythonWrapperCodegen,
) -> tuple[str, str]:
    """
    Retrieves metadata information for a kernel.
    Args:
        node_schedule (Union[Sequence[BaseSchedulerNode], ExternKernel]):
            Either a sequence of BaseSchedulerNode objects or an ExternKernel instance.
        wrapper (PythonWrapperCodegen):
            An instance of PythonWrapperCodegen, used to define the code comment format.
    Returns:
        tuple[str, str]:
            A tuple containing two strings:
                - The first string represents the kernel's metadata.
                - The second string represent the kernel's detailed metadata.
    """

    all_origins = aggregate_origins(node_schedule)
    inductor_nodes = [origin for origin in all_origins if origin.op == "call_function"]

    from_node_dict = collections.defaultdict(list)
    original_aten_dict = collections.defaultdict(list)

    # Attempt to sort `inductor_nodes` topologically. Note that the case
    # where `inductor_nodes` contains nodes from multiple graph instances
    # is not supported. An example of this is conditional statements.
    single_graph = None
    if inductor_nodes:
        unique_graphs = OrderedSet(n.graph for n in inductor_nodes)
        if len(unique_graphs) == 1:
            single_graph = inductor_nodes[0].graph
            # create a map of idx -> node and cache it
            if not hasattr(single_graph, "_inductor_kernel_metadata_node_to_idx_map"):
                node_to_idx_map = {n: idx for idx, n in enumerate(single_graph.nodes)}
                single_graph._inductor_kernel_metadata_node_to_idx_map = node_to_idx_map  # type: ignore[attr-defined]
            inductor_nodes.sort(
                key=lambda n: single_graph._inductor_kernel_metadata_node_to_idx_map[n]  # type: ignore[attr-defined]
            )

    for node in inductor_nodes:
        if "original_aten" in node.meta and node.meta["original_aten"] is not None:
            original_aten = node.meta["original_aten"]
            key = None
            if isinstance(original_aten, torch._ops.OpOverload):
                key = str(original_aten._overloadpacket)
            elif isinstance(original_aten, torch._ops.HigherOrderOperator):
                key = str(original_aten.name())
            if key:
                original_aten_dict[key].append(node.name)
        if "from_node" in node.meta:
            key = node.meta["from_node"][0].name
            from_node_dict[key].append(node.name)
        elif node.meta.get("partitioner_tag") == "is_backward":
            # backward nodes currently don't have a "from node"
            from_node_dict[node.name].append(node.name)
    sort_str = "Topologically Sorted" if single_graph is not None else "Unsorted"
    metadata = (
        f"{wrapper.comment} {sort_str} Source Nodes: [{', '.join(from_node_dict.keys())}], "
        f"Original ATen: [{', '.join(original_aten_dict.keys())}]"
    )

    # trace back to original node here
    detailed_metadata = [f"{wrapper.comment} Source node to ATen node mapping:"]
    for original_node, nodes in sorted(from_node_dict.items()):
        detailed_metadata.append(
            f"{wrapper.comment}   {original_node} => {', '.join(sorted(nodes))}"
        )

    # print the aot_autograd graph fragment
    if single_graph is not None:
        from . import ir

        detailed_metadata.append(f"{wrapper.comment} Graph fragment:")
        all_reads: OrderedSet[str] = OrderedSet()
        all_writes: list[str] = []
        if not isinstance(node_schedule, ir.ExternKernel):
            from .virtualized import V

            def get_buffer_info(
                buffer: ir.TensorBox | ir.Buffer | ir.TorchBindObject, rw_name: str
            ) -> tuple[str, ir.Layout | None]:
                if isinstance(buffer, ir.TensorBox) and isinstance(
                    buffer.data, ir.StorageBox
                ):
                    origin_node = buffer.data.data.origin_node
                else:
                    origin_node = buffer.origin_node
                if origin_node is None:
                    # use the read/write name if no origin node is found
                    name = rw_name
                else:
                    name = origin_node.name
                try:
                    layout = buffer.get_layout()
                except NotImplementedError:
                    layout = None
                return name, layout

            def stringify_shape(shape: Iterable[int]) -> str:
                return f"[{', '.join([str(x) for x in shape])}]"

            def stringfy_layout(layout: ir.Layout | None) -> str:
                if layout is None:
                    return ""
                shape_annotation = f"{stringify_shape(layout.size)}"
                stride_annotation = f"{stringify_shape(layout.stride)}"
                device_annotation = f"{layout.device}"

                return (
                    f'"{dtype_abbrs[layout.dtype]}{shape_annotation}'
                    f'{stride_annotation}{device_annotation}"'
                )

            for n in node_schedule:
                if not hasattr(n, "read_writes") or n.read_writes is None:
                    continue
                if hasattr(n.read_writes, "reads") and n.read_writes.reads is not None:
                    for r in n.read_writes.reads:
                        # Remove the dupricated inputs
                        if r.name in all_reads:
                            continue
                        all_reads.add(r.name)
                        buffer = V.graph.try_get_buffer(r.name)
                        if buffer is None:
                            continue
                        input_name, layout = get_buffer_info(buffer, r.name)
                        detailed_metadata.append(
                            f"{wrapper.comment}   %{input_name} : Tensor "
                            f"{stringfy_layout(layout)} = PlaceHolder[target={input_name}]"
                        )

                if (
                    hasattr(n.read_writes, "writes")
                    and n.read_writes.writes is not None
                ):
                    for w in n.read_writes.writes:
                        buffer = V.graph.try_get_buffer(w.name)
                        if buffer is None:
                            continue
                        output_name, _ = get_buffer_info(buffer, w.name)

                        all_writes.append("%" + output_name)

        for node in inductor_nodes:
            formatted_node = node.format_node(include_tensor_metadata=True)
            if formatted_node is not None and torch.version.hip:
                # AMDGCN asm strings can contain newlines, which propagate
                # into format_node() output.  Split so every line gets the
                # comment prefix; otherwise bare newlines break the wrapper.
                detailed_metadata.extend(
                    f"{wrapper.comment}   {line}"
                    for line in formatted_node.splitlines()
                )
            else:
                detailed_metadata.append(f"{wrapper.comment}   {formatted_node}")

        detailed_metadata.append(f"{wrapper.comment}   return {','.join(all_writes)}")

    return metadata, "\n".join(detailed_metadata)