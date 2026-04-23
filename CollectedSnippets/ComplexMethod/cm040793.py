def _traverse_policy(obj, array=None, parent_key=None) -> list:
            if array is None:
                array = [{}]

            for key, values in obj.items():
                if key == "$or" and isinstance(values, list) and len(values) > 1:
                    # $or will create multiple new branches in the array.
                    # Each current branch will traverse with each choice in $or
                    array = [
                        i for value in values for i in _traverse_policy(value, array, parent_key)
                    ]
                else:
                    # We update the parent key do that {"key1": {"key2": ""}} becomes "key1.key2"
                    _parent_key = f"{parent_key}.{key}" if parent_key else key
                    if isinstance(values, dict):
                        # If the current key has child dict -- key: "key1", child: {"key2": ["val1", val2"]}
                        # We only update the parent_key and traverse its children with the current branches
                        array = _traverse_policy(values, array, _parent_key)
                    else:
                        # If the current key has no child, this means we found the values to match -- child: ["val1", val2"]
                        # we update the branches with the parent chain and the values -- {"key1.key2": ["val1, val2"]}
                        array = [{**item, _parent_key: values} for item in array]

            return array