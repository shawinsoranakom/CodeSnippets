def test_to_unique_item_list(self):
        assert common.to_unique_items_list([1, 1, 2, 2, 3]) == [1, 2, 3]
        assert common.to_unique_items_list(["a"]) == ["a"]
        assert common.to_unique_items_list(["a", "b", "a"]) == ["a", "b"]
        assert common.to_unique_items_list("aba") == ["a", "b"]
        assert common.to_unique_items_list([]) == []

        def comparator_lower(first, second):
            return first.lower() == second.lower()

        assert common.to_unique_items_list(["a", "A", "a"]) == ["a", "A"]
        assert common.to_unique_items_list(["a", "A", "a"], comparator_lower) == ["a"]
        assert common.to_unique_items_list(["a", "A", "a"], comparator_lower) == ["a"]

        def comparator_str_int(first, second):
            return int(first) - int(second)

        assert common.to_unique_items_list(["1", "2", "1", "2"], comparator_str_int) == ["1", "2"]