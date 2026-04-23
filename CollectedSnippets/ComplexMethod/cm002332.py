def find_all_dependencies(
    dependency_mapping: dict[str, set],
    start_entity: str | None = None,
    initial_dependencies: set | None = None,
    initial_checked_dependencies: set | None = None,
    return_parent: bool = False,
) -> list | set:
    """Return all the dependencies of the given `start_entity` or `initial_dependencies`. This is basically some kind of
    BFS traversal algorithm. It can either start from `start_entity`, or `initial_dependencies`.

    Args:
        dependency_mapping (`Dict[str, set]`):
            A mapping from entities (usually function/assignment names), to immediate dependencies. That is, for function names,
            a mapping {"foo": {"bar", "test"}} would indicate that functions `bar` and `test` are immediately called
            in `foo`'s definition.
        start_entity (str | None, *optional*):
            A key of `dependency_mapping`, indicating from which entity to start the search.
        initial_dependencies (set | None, *optional*):
            If `start_entity` is not provided, this can be used as an alternative. In this case, the search will continue
            from all the entities in `initial_dependencies`, if they are in `dependency_mapping`.
        initial_checked_dependencies (set | None, *optional*):
            If provided, entities already present in `initial_checked_dependencies` will not be part of the returned dependencies.
        return_parent (bool, *optional*):
            If `True`, will return a list consisting of tuples (dependency, parent) instead of a simple set of dependencies. Note
            that the order of the items in the list reflects the traversal order. Thus, no parent can ever appear before children.
    Returns:
        A set of all the dependencies, or a list of tuples `(dependency, parent)` if `return_parent=True`.

    Example:
    Given the following structure in the `modular_xxx.py` file:
    ```
    def foo1():
        pass

    def foo2():
        pass

    def bar():
        foo1()

    def foobar():
        bar()
        foo2()

    class MyLayer(SomeOtherModelLayer):
        def forward(...):
            foobar()
    ```
    and the `dependency_mapping` created when visiting the `modular_xxx.py` file, we get:
    ```
    dependency_mapping = {'bar': {'foo1'}, 'foobar': {'bar', 'foo2'}}
    find_all_dependencies(dependency_mapping, start_entity='foobar', return_parent=True)
    >>> [('bar', 'foobar'), ('foo2', 'foobar'), ('foo1', 'bar')]
    ```
    That is, all the functions needed (and potentially their immediate parent) so that the function to be added
    in MyLayer (`foobar`) can work correctly.
    """
    if initial_dependencies is None and start_entity is not None:
        initial_dependencies = dependency_mapping[start_entity]
    if initial_checked_dependencies is None:
        initial_checked_dependencies = set()

    dependency_queue = deque(initial_dependencies)
    all_dependencies = set()
    all_dependencies_with_parent = []
    checked_dependencies = set(initial_checked_dependencies)
    parents = dict.fromkeys(initial_dependencies, start_entity)
    while len(dependency_queue) > 0:
        # Pick element to visit
        current = dependency_queue.popleft()
        if current not in checked_dependencies:
            # Add the dependencies
            all_dependencies.add(current)
            all_dependencies_with_parent += [(current, parents[current])]
            if current in dependency_mapping:
                # Update dependency queue
                dependency_queue.extend(dependency_mapping[current])
                parents.update(dict.fromkeys(dependency_mapping[current], current))
            # add visited node to the list
            checked_dependencies.add(current)

    if not return_parent:
        return all_dependencies
    # no child can ever appear before its parent thanks to the queue (needed to add them at the correct location in the body later)
    return all_dependencies_with_parent