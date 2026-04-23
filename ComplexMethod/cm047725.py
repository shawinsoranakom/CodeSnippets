def __combine(leaves: Iterable[Leaf], leaves_to_add: Iterable[Leaf]) -> list[Leaf]:
        """ Combine some existing intersection of leaves with extra leaves. """
        result = list(leaves)
        for leaf_to_add in leaves_to_add:
            for index, leaf in enumerate(result):
                if leaf.isdisjoint(leaf_to_add):  # leaf & leaf_to_add = empty
                    return [EMPTY_LEAF]
                if leaf <= leaf_to_add:  # leaf & leaf_to_add = leaf
                    break
                if leaf_to_add <= leaf:  # leaf & leaf_to_add = leaf_to_add
                    result[index] = leaf_to_add
                    break
            else:
                if not leaf_to_add.is_universal():
                    result.append(leaf_to_add)
        return result