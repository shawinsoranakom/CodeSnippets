def _build_tree(id2name, awaits, task_stacks):
    id2label = {(NodeType.TASK, tid): name for tid, name in id2name.items()}
    children = defaultdict(list)
    cor_nodes = defaultdict(dict)  # Maps parent -> {frame_name: node_key}
    next_cor_id = count(1)

    def get_or_create_cor_node(parent, frame):
        """Get existing coroutine node or create new one under parent"""
        if frame in cor_nodes[parent]:
            return cor_nodes[parent][frame]

        node_key = (NodeType.COROUTINE, f"c{next(next_cor_id)}")
        id2label[node_key] = frame
        children[parent].append(node_key)
        cor_nodes[parent][frame] = node_key
        return node_key

    # Build task dependency tree with coroutine frames
    for parent_id, stack, child_id in awaits:
        cur = (NodeType.TASK, parent_id)
        for frame in reversed(stack):
            cur = get_or_create_cor_node(cur, frame)

        child_key = (NodeType.TASK, child_id)
        if child_key not in children[cur]:
            children[cur].append(child_key)

    # Add coroutine stacks for leaf tasks
    awaiting_tasks = {parent_id for parent_id, _, _ in awaits}
    for task_id in id2name:
        if task_id not in awaiting_tasks and task_id in task_stacks:
            cur = (NodeType.TASK, task_id)
            for frame in reversed(task_stacks[task_id]):
                cur = get_or_create_cor_node(cur, frame)

    return id2label, children