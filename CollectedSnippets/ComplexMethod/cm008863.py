def dependents_graph() -> dict:
    """Construct a mapping of package -> dependents

    Done such that we can run tests on all dependents of a package when a change is made.
    """
    dependents = defaultdict(set)

    for path in glob.glob("./libs/**/pyproject.toml", recursive=True):
        if "template" in path:
            continue

        # load regular and test deps from pyproject.toml
        with open(path, "rb") as f:
            pyproject = tomllib.load(f)

        pkg_dir = "libs" + "/".join(path.split("libs")[1].split("/")[:-1])
        for dep in [
            *pyproject["project"]["dependencies"],
            *pyproject["dependency-groups"]["test"],
        ]:
            requirement = Requirement(dep)
            package_name = requirement.name
            if "langchain" in dep:
                dependents[package_name].add(pkg_dir)
                continue

        # load extended deps from extended_testing_deps.txt
        package_path = Path(path).parent
        extended_requirement_path = package_path / "extended_testing_deps.txt"
        if extended_requirement_path.exists():
            with open(extended_requirement_path, "r") as f:
                extended_deps = f.read().splitlines()
                for depline in extended_deps:
                    if depline.startswith("-e "):
                        # editable dependency
                        assert depline.startswith("-e ../partners/"), (
                            "Extended test deps should only editable install partner packages"
                        )
                        partner = depline.split("partners/")[1]
                        dep = f"langchain-{partner}"
                    else:
                        dep = depline.split("==")[0]

                    if "langchain" in dep:
                        dependents[dep].add(pkg_dir)

    for k in dependents:
        for partner in IGNORED_PARTNERS:
            if f"libs/partners/{partner}" in dependents[k]:
                dependents[k].remove(f"libs/partners/{partner}")
    return dependents