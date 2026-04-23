def apriori(data: list[list[str]], min_support: int) -> list[tuple[list[str], int]]:
    """
    Returns a list of frequent itemsets and their support counts.

    >>> data = [['A', 'B', 'C'], ['A', 'B'], ['A', 'C'], ['A', 'D'], ['B', 'C']]
    >>> apriori(data, 2)
    [(['A', 'B'], 1), (['A', 'C'], 2), (['B', 'C'], 2)]

    >>> data = [['1', '2', '3'], ['1', '2'], ['1', '3'], ['1', '4'], ['2', '3']]
    >>> apriori(data, 3)
    []
    """
    itemset = [list(transaction) for transaction in data]
    frequent_itemsets = []
    length = 1

    while itemset:
        # Count itemset support
        counts = [0] * len(itemset)
        for transaction in data:
            for j, candidate in enumerate(itemset):
                if all(item in transaction for item in candidate):
                    counts[j] += 1

        # Prune infrequent itemsets
        itemset = [item for i, item in enumerate(itemset) if counts[i] >= min_support]

        # Append frequent itemsets (as a list to maintain order)
        for i, item in enumerate(itemset):
            frequent_itemsets.append((sorted(item), counts[i]))

        length += 1
        itemset = prune(itemset, list(combinations(itemset, length)), length)

    return frequent_itemsets