def load_from_library(library, label, names):
    """
    Return a subset of tags and filters from a library.
    """
    subset = Library()
    for name in names:
        found = False
        if name in library.tags:
            found = True
            subset.tags[name] = library.tags[name]
        if name in library.filters:
            found = True
            subset.filters[name] = library.filters[name]
        if found is False:
            raise TemplateSyntaxError(
                "'%s' is not a valid tag or filter in tag library '%s'"
                % (
                    name,
                    label,
                ),
            )
    return subset