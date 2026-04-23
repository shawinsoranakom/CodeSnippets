def _validate_selection(selection, valid_values, name):
        """Validate country or counterpart selection."""
        if not valid_values:
            return selection

        # Handle wildcards - return "*" as-is
        if selection == "*":
            return "*"

        # Parse the selection into a list
        if isinstance(selection, str):
            # Check if it contains commas (comma-separated list)
            selection_list = (
                [item.strip() for item in selection.split(",")]
                if "," in selection
                else [selection]
            )
        else:
            selection_list = selection

        # Check if any item is a wildcard
        if "*" in selection_list:
            return "*"

        invalid = [item for item in selection_list if item not in valid_values]
        if invalid:
            raise ValueError(f"Invalid {name}(s): {', '.join(invalid)}")
        return selection_list if len(selection_list) > 1 else selection_list[0]