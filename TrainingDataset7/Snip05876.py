def cell_count(inline_admin_form):
    """Return the number of cells used in a tabular inline."""
    count = 1  # Hidden cell with hidden 'id' field
    for fieldset in inline_admin_form:
        # Count all visible fields.
        for line in fieldset:
            for field in line:
                try:
                    is_hidden = field.field.is_hidden
                except AttributeError:
                    is_hidden = field.field["is_hidden"]
                if not is_hidden:
                    count += 1
    if inline_admin_form.formset.can_delete:
        # Delete checkbox
        count += 1
    return count