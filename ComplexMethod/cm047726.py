def _union_merge(self, other: Inter) -> Inter | None:
        """ Return the union of ``self`` with another intersection, if it can be
        represented as an intersection. Otherwise return ``None``.
        """
        # the following covers cases like (A & B) | A -> A
        if self.is_universal() or other <= self:
            return self
        if self <= other:
            return other

        # combine complementary parts: (A & ~B) | (A & B) -> A
        if len(self.leaves) == len(other.leaves):
            opposite_index = None
            # we use the property that __leaves are ordered
            for index, self_leaf, other_leaf in zip(range(len(self.leaves)), self.leaves, other.leaves):
                if self_leaf.id != other_leaf.id:
                    return None
                if self_leaf.negative != other_leaf.negative:
                    if opposite_index is not None:
                        return None  # we already have two opposite leaves
                    opposite_index = index
            if opposite_index is not None:
                leaves = list(self.leaves)
                leaves.pop(opposite_index)
                return Inter(leaves, optimal=True)
        return None