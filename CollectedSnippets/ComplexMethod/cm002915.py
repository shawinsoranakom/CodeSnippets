def _get_nested_dimensions(self, nested_list, max_dims=None):
        """
        Get the maximum dimensions at each level of nesting, skipping None values.

        Args:
            nested_list (`list`):
                Nested list structure (may contain None values).
            max_dims (`list`, *optional*):
                Current maximum dimensions (for recursion).

        Returns:
            `list`: A list of maximum dimensions for each nesting level.
        """
        if max_dims is None:
            max_dims = []

        if not isinstance(nested_list, list):
            return max_dims

        if len(max_dims) == 0:
            max_dims.append(len(nested_list))
        else:
            max_dims[0] = max(max_dims[0], len(nested_list))

        if len(nested_list) > 0:
            for item in nested_list:
                # Skip None values
                if item is None:
                    continue
                if isinstance(item, list):
                    sub_dims = self._get_nested_dimensions(item)
                    # Merge sub_dims into max_dims
                    for i, dim in enumerate(sub_dims):
                        if i + 1 >= len(max_dims):
                            max_dims.append(dim)
                        else:
                            max_dims[i + 1] = max(max_dims[i + 1], dim)

        return max_dims