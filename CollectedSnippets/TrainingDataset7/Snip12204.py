def rename_prefix_from_q(prefix, replacement, q):
    return Q.create(
        [get_child_with_renamed_prefix(prefix, replacement, c) for c in q.children],
        q.connector,
        q.negated,
    )