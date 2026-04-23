def describe_operation(operation, backwards):
        """Return a string that describes a migration operation for --plan."""
        prefix = ""
        is_error = False
        if hasattr(operation, "code"):
            code = operation.reverse_code if backwards else operation.code
            action = (code.__doc__ or "") if code else None
        elif hasattr(operation, "sql"):
            action = operation.reverse_sql if backwards else operation.sql
        else:
            action = ""
            if backwards:
                prefix = "Undo "
        if action is not None:
            action = str(action).replace("\n", "")
        elif backwards:
            action = "IRREVERSIBLE"
            is_error = True
        if action:
            action = " -> " + action
        truncated = Truncator(action)
        return prefix + operation.describe() + truncated.chars(40), is_error