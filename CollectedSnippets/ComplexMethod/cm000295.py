def create_tree(data_set: list, min_sup: int = 1) -> tuple[TreeNode, dict]:
    """
    Create Frequent Pattern tree

    Args:
        data_set: A list of transactions, where each transaction is a list of items.
        min_sup: The minimum support threshold.
        Items with support less than this will be pruned. Default is 1.

    Returns:
        The root of the FP-Tree.
        header_table: The header table dictionary with item information.

    Example:
    >>> data_set = [
    ...    ['A', 'B', 'C'],
    ...    ['A', 'C'],
    ...    ['A', 'B', 'E'],
    ...    ['A', 'B', 'C', 'E'],
    ...    ['B', 'E']
    ... ]
    >>> min_sup = 2
    >>> fp_tree, header_table = create_tree(data_set, min_sup)
    >>> fp_tree
    TreeNode('Null Set', 1, None)
    >>> len(header_table)
    4
    >>> header_table["A"]
    [[4, None], TreeNode('A', 4, TreeNode('Null Set', 1, None))]
    >>> header_table["E"][1]  # doctest: +NORMALIZE_WHITESPACE
    TreeNode('E', 1, TreeNode('B', 3, TreeNode('A', 4, TreeNode('Null Set', 1, None))))
    >>> sorted(header_table)
    ['A', 'B', 'C', 'E']
    >>> fp_tree.name
    'Null Set'
    >>> sorted(fp_tree.children)
    ['A', 'B']
    >>> fp_tree.children['A'].name
    'A'
    >>> sorted(fp_tree.children['A'].children)
    ['B', 'C']
    """
    header_table: dict = {}
    for trans in data_set:
        for item in trans:
            header_table[item] = header_table.get(item, [0, None])
            header_table[item][0] += 1

    for k in list(header_table):
        if header_table[k][0] < min_sup:
            del header_table[k]

    if not (freq_item_set := set(header_table)):
        return TreeNode("Null Set", 1, None), {}

    for key, value in header_table.items():
        header_table[key] = [value, None]

    fp_tree = TreeNode("Null Set", 1, None)  # Parent is None for the root node
    for tran_set in data_set:
        local_d = {
            item: header_table[item][0] for item in tran_set if item in freq_item_set
        }
        if local_d:
            sorted_items = sorted(
                local_d.items(), key=lambda item_info: item_info[1], reverse=True
            )
            ordered_items = [item[0] for item in sorted_items]
            update_tree(ordered_items, fp_tree, header_table, 1)

    return fp_tree, header_table