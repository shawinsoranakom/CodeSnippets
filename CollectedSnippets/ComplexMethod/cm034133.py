def get_all_subclasses(cls: type[_Type], *, include_abstract: bool = True, consider_self: bool = False) -> set[type[_Type]]:
    """Recursively find all subclasses of a given type, including abstract classes by default."""
    subclasses: set[type[_Type]] = {cls} if consider_self else set()
    queue: list[type[_Type]] = [cls]

    while queue:
        parent = queue.pop()

        for child in parent.__subclasses__():
            if child in subclasses:
                continue

            queue.append(child)
            subclasses.add(child)

    if not include_abstract:
        subclasses = {sc for sc in subclasses if not inspect.isabstract(sc)}

    return subclasses