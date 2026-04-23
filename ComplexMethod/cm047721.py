def __init__(self, definitions: dict[int, dict]):
        """ Initialize the object with ``definitions``, a dict which maps each
        set id to a dict with optional keys ``"ref"`` (value is the set's name),
        ``"supersets"`` (value is a collection of set ids), and ``"disjoints"``
        (value is a collection of set ids).

        Here is an example of set definitions, with natural numbers (N), integer
        numbers (Z), rational numbers (Q), irrational numbers (R\\Q), real
        numbers (R), imaginary numbers (I) and complex numbers (C)::

            {
                1: {"ref": "N", "supersets": [2]},
                2: {"ref": "Z", "supersets": [3]},
                3: {"ref": "Q", "supersets": [4]},
                4: {"ref": "R", "supersets": [6]},
                5: {"ref": "I", "supersets": [6], "disjoints": [4]},
                6: {"ref": "C"},
                7: {"ref": "R\\Q", "supersets": [4]},
            }
            Representation:
            ┌──────────────────────────────────────────┐
            │ C  ┌──────────────────────────┐          │
            │    │ R  ┌───────────────────┐ │ ┌──────┐ |   "C"
            │    │    │ Q  ┌────────────┐ │ │ │ I    | |   "I" implied "C"
            │    │    │    │ Z  ┌─────┐ │ │ │ │      | |   "R" implied "C"
            │    │    │    │    │ N   │ │ │ │ │      │ │   "Q" implied "R"
            │    │    │    │    └─────┘ │ │ │ │      │ │   "R\\Q" implied "R"
            │    │    │    └────────────┘ │ │ │      │ │   "Z" implied "Q"
            │    │    └───────────────────┘ │ │      │ │   "N" implied "Z"
            │    │      ┌───────────────┐   │ │      │ │
            │    │      │ R\\Q          │   │ │      │ │
            │    │      └───────────────┘   │ └──────┘ │
            │    └──────────────────────────┘          │
            └──────────────────────────────────────────┘
        """
        self.__leaves: dict[int | str, Leaf] = {}

        for leaf_id, info in definitions.items():
            ref = info['ref']
            assert ref != '*', "The set reference '*' is reserved for the universal set."
            leaf = Leaf(leaf_id, ref)
            self.__leaves[leaf_id] = leaf
            self.__leaves[ref] = leaf

        # compute transitive closure of subsets and supersets
        subsets = {leaf.id: leaf.subsets for leaf in self.__leaves.values()}
        supersets = {leaf.id: leaf.supersets for leaf in self.__leaves.values()}
        for leaf_id, info in definitions.items():
            for greater_id in info.get('supersets', ()):
                # transitive closure: smaller_ids <= leaf_id <= greater_id <= greater_ids
                smaller_ids = subsets[leaf_id]
                greater_ids = supersets[greater_id]
                for smaller_id in smaller_ids:
                    supersets[smaller_id].update(greater_ids)
                for greater_id in greater_ids:
                    subsets[greater_id].update(smaller_ids)

        # compute transitive closure of disjoint relation
        disjoints = {leaf.id: leaf.disjoints for leaf in self.__leaves.values()}
        for leaf_id, info in definitions.items():
            for distinct_id in info.get('disjoints', set()):
                # all subsets[leaf_id] are disjoint from all subsets[distinct_id]
                left_ids = subsets[leaf_id]
                right_ids = subsets[distinct_id]
                for left_id in left_ids:
                    disjoints[left_id].update(right_ids)
                for right_id in right_ids:
                    disjoints[right_id].update(left_ids)