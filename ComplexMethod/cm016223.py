def wrap_body_with_streams(
        generated_code_lines: list[str],
        graph: OperationGraph,
    ) -> list[str]:
        """Wrap generated function body lines with CUDA stream contexts.

        Assigns each non-leaf operation to one of 2-3 random streams, wraps each
        in ``with torch.cuda.stream(sN):``, and inserts ``wait_stream`` calls
        between dependent operations on different streams.
        """
        topo_order = graph.get_topological_order()

        # Identify leaf vs non-leaf node ids
        leaf_ids = set()
        non_leaf_ids = []
        for nid in topo_order:
            node = graph.nodes[nid]
            if (
                node.op_name == "arg"
                or node.op_name.startswith("arg_")
                or node.op_name == "constant"
            ):
                leaf_ids.add(nid)
            else:
                non_leaf_ids.append(nid)

        if not non_leaf_ids:
            return generated_code_lines

        num_streams = random.randint(2, 3)
        stream_names = [f"s{i + 1}" for i in range(num_streams)]

        # Decide sync strategy: wait_stream or event-based (record + wait_event)
        use_events = random.choice([True, False])
        event_counter = 0

        # Assign each non-leaf node to a random stream
        node_stream: dict[str, str] = {}
        for nid in non_leaf_ids:
            node_stream[nid] = random.choice(stream_names)

        # Build a mapping from node_id -> the original code lines for that node.
        # Each node produces lines prefixed with "    " (4-space indent for the
        # function body).  We identify nodes by their ``var_{node_id} =`` pattern.
        node_lines: dict[str, list[str]] = {}
        current_node: str | None = None
        current_buf: list[str] = []

        for line in generated_code_lines:
            stripped = line.strip()
            # Detect lines like "var_node_3 = ..." or "var_node_3, _ = ..."
            matched_node = None
            for nid in topo_order:
                if stripped.startswith((f"var_{nid} =", f"var_{nid},")):
                    matched_node = nid
                    break

            if matched_node is not None:
                # Flush previous node buffer
                if current_node is not None:
                    node_lines[current_node] = current_buf
                current_node = matched_node
                current_buf = [line]
            else:
                current_buf.append(line)

        # Flush last node
        if current_node is not None:
            node_lines[current_node] = current_buf

        # Rebuild the body with stream contexts and synchronization
        new_lines: list[str] = []

        # Stream variable declarations at the top of the function body
        for sname in stream_names:
            new_lines.append(f"    {sname} = torch.cuda.Stream()")

        for nid in topo_order:
            lines_for_node = node_lines.get(nid, [])
            if nid in leaf_ids:
                # Leaf nodes (args) stay on the default stream
                new_lines.extend(lines_for_node)
                continue

            stream = node_stream[nid]
            node = graph.nodes[nid]

            # Insert synchronization for cross-stream dependencies
            waited: set[str] = set()
            for dep_id in node.input_nodes:
                if dep_id in node_stream and node_stream[dep_id] != stream:
                    dep_stream = node_stream[dep_id]
                    if dep_stream not in waited:
                        if use_events:
                            ename = f"e{event_counter}"
                            event_counter += 1
                            new_lines.append(f"    {ename} = torch.cuda.Event()")
                            new_lines.append(f"    {ename}.record({dep_stream})")
                            new_lines.append(f"    {stream}.wait_event({ename})")
                        else:
                            new_lines.append(f"    {stream}.wait_stream({dep_stream})")
                        waited.add(dep_stream)

            # Wrap the operation in a stream context
            new_lines.append(f"    with torch.cuda.stream({stream}):")
            for code_line in lines_for_node:
                # Each line already has 4-space indent; add 4 more for the with block
                new_lines.append("    " + code_line)

        # Synchronize all streams before the return statement
        if use_events:
            for sname in stream_names:
                ename = f"e{event_counter}"
                event_counter += 1
                new_lines.append(f"    {ename} = torch.cuda.Event()")
                new_lines.append(f"    {ename}.record({sname})")
                new_lines.append(f"    torch.cuda.current_stream().wait_event({ename})")
        else:
            for sname in stream_names:
                new_lines.append(
                    f"    torch.cuda.current_stream().wait_stream({sname})"
                )

        return new_lines