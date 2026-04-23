def create_reverse_dependency_map() -> dict[str, list[str]]:
    """
    Create the dependency map from module/test filename to the list of modules/tests that depend on it recursively.

    Returns:
        `Dict[str, List[str]]`: The reverse dependency map as a dictionary mapping filenames to all the filenames
        depending on it recursively. This way the tests impacted by a change in file A are the test files in the list
        corresponding to key A in this result.
    """

    cache = {}
    # Start from the example deps init.
    example_deps, examples = init_test_examples_dependencies()
    # Add all modules and all tests to all examples
    all_modules = list(PATH_TO_TRANSFORMERS.glob("**/*.py"))
    all_modules = [x for x in all_modules if not ("models" in x.parts and x.parts[-1].startswith("convert_"))]
    all_modules += list(PATH_TO_TESTS.glob("**/*.py")) + examples
    all_modules = [str(mod.relative_to(PATH_TO_REPO)) for mod in all_modules]
    # Compute the direct dependencies of all modules.
    direct_deps = {m: get_module_dependencies(m, cache=cache) for m in all_modules}
    direct_deps.update(example_deps)

    # This recurses the dependencies
    something_changed = True
    while something_changed:
        something_changed = False
        for m in all_modules:
            for d in direct_deps[m]:
                # We stop recursing at an init (cause we always end up in the main init and we don't want to add all
                # files which the main init imports)
                if d.endswith("__init__.py"):
                    continue
                if d not in direct_deps:
                    raise ValueError(f"KeyError:{d}. From {m}")
                new_deps = set(direct_deps[d]) - set(direct_deps[m])
                if len(new_deps) > 0:
                    direct_deps[m].extend(list(new_deps))
                    something_changed = True

    # Finally we can build the reverse map.
    reverse_map = collections.defaultdict(list)
    for m in all_modules:
        for d in direct_deps[m]:
            reverse_map[d].append(m)

    # For inits, we don't do the reverse deps but the direct deps: if modifying an init, we want to make sure we test
    # all the modules impacted by that init.
    for m in [f for f in all_modules if f.endswith("__init__.py")]:
        direct_deps = get_module_dependencies(m, cache=cache)
        deps = sum((reverse_map[d] for d in direct_deps if not d.endswith("__init__.py")), direct_deps)
        reverse_map[m] = list(set(deps) - {m})

    return reverse_map