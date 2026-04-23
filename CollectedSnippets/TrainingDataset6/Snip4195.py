def get_scopes(
    dep3: Annotated[dict[str, Any], Security(dep3, scopes=["scope3"])],
):
    return dep3