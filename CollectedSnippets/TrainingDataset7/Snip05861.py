def search_form(cl):
    """
    Display a search form for searching the list.
    """
    return {
        "cl": cl,
        "show_result_count": cl.result_count != cl.full_result_count,
        "search_var": SEARCH_VAR,
        "is_popup_var": IS_POPUP_VAR,
        "is_facets_var": IS_FACETS_VAR,
    }