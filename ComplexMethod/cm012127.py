def find_and_instantiate_subclasses(
    package_name: str, base_class: Any
) -> list[LearnedHeuristic]:
    instances = []

    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        try:
            module_basename = module_name.split(".")[-1]
            if not module_basename.startswith("_"):
                # learned heuristics start with an underscore
                continue
            module = importlib.import_module(module_name)

            # look for classes that are subclasses of base_class
            for _name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, base_class)
                    and obj != base_class
                ):
                    instance = obj()
                    instances.append(instance)
        except Exception as e:
            print(f"Error processing module {module_name}: {e}")

    return instances