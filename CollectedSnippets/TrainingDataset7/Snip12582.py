def all_valid(formsets):
    """Validate every formset and return True if all are valid."""
    # List comprehension ensures is_valid() is called for all formsets.
    return all([formset.is_valid() for formset in formsets])