def _pad_nested_list(self, nested_list, target_dims, current_level=0, pad_value=None):
        """
        Recursively pad a nested list to match target dimensions.

        Args:
            nested_list (`list`):
                Nested list to pad.
            target_dims (`list`):
                Target dimensions for each level.
            current_level (`int`, *optional*, defaults to 0):
                Current nesting level.
            pad_value (`int`, *optional*):
                Value to use for padding.

        Returns:
            `list`: The padded nested list.
        """
        if pad_value is None:
            pad_value = self.point_pad_value

        if current_level >= len(target_dims):
            return nested_list

        # Ensure we have a list
        if not isinstance(nested_list, list):
            nested_list = [nested_list]

        # Pad current level
        current_size = len(nested_list)
        target_size = target_dims[current_level]

        # Pad with appropriate values
        if current_level == len(target_dims) - 1:
            # At the coordinate level, pad with pad_value
            nested_list.extend([pad_value] * (target_size - current_size))
        else:
            # At higher levels, pad with nested structures
            if current_size > 0:
                # Create appropriately sized template
                if current_level < len(target_dims) - 2:
                    # For non-coordinate levels, create empty nested structure
                    template_dims = target_dims[current_level + 1 :]
                    template = self._create_empty_nested_structure(template_dims, pad_value)
                else:
                    # For coordinate level, create list of pad_values
                    template = [pad_value] * target_dims[current_level + 1]

                nested_list.extend([deepcopy(template) for _ in range(target_size - current_size)])
            else:
                # Create from scratch
                template_dims = target_dims[current_level + 1 :]
                template = self._create_empty_nested_structure(template_dims, pad_value)
                nested_list.extend([deepcopy(template) for _ in range(target_size)])

        # Recursively pad sublists
        if current_level < len(target_dims) - 1:
            for i in range(len(nested_list)):
                if isinstance(nested_list[i], list):
                    nested_list[i] = self._pad_nested_list(nested_list[i], target_dims, current_level + 1, pad_value)

        return nested_list