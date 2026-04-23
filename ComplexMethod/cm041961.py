def new_agent_retrieve(role, focus_points: list, n_count=30) -> dict:
    """
    输入为role，关注点列表,返回记忆数量
    输出为字典，键为focus_point，值为对应的记忆列表
    """
    retrieved = dict()
    for focal_pt in focus_points:
        nodes = [
            [i.last_accessed, i]
            for i in role.memory.event_list + role.memory.thought_list
            if "idle" not in i.embedding_key
        ]
        nodes = sorted(nodes, key=lambda x: x[0])
        nodes = [i for created, i in nodes]
        results = agent_retrieve(
            role.memory, role.scratch.curr_time, role.scratch.recency_decay, focal_pt, nodes, n_count
        )
        final_result = []
        for n in results:
            for i in role.memory.storage:
                if i.memory_id == n:
                    i.last_accessed = role.scratch.curr_time
                    final_result.append(i)

        retrieved[focal_pt] = final_result

    return retrieved