def create_import_structure_from_path(module_path):
    """
    This method takes the path to a file/a folder and returns the import structure.
    If a file is given, it will return the import structure of the parent folder.

    Import structures are designed to be digestible by `_LazyModule` objects. They are
    created from the __all__ definitions in each files as well as the `@require` decorators
    above methods and objects.

    The import structure allows explicit display of the required backends for a given object.
    These backends are specified in two ways:

    1. Through their `@require`, if they are exported with that decorator. This `@require` decorator
       accepts a `backend` tuple kwarg mentioning which backends are required to run this object.

    2. If an object is defined in a file with "default" backends, it will have, at a minimum, this
       backend specified. The default backends are defined according to the filename:

       - If a file is named like `modeling_*.py`, it will have a `torch` backend
       - If a file is named like `tokenization_*_fast.py`, it will have a `tokenizers` backend
       - If a file is named like `image_processing*_fast.py`, it will have a `torchvision` + `torch` backend

    Backends serve the purpose of displaying a clear error message to the user in case the backends are not installed.
    Should an object be imported without its required backends being in the environment, any attempt to use the
    object will raise an error mentioning which backend(s) should be added to the environment in order to use
    that object.

    Here's an example of an input import structure at the src.transformers.models level:

    {
        'albert': {
            frozenset(): {
                'configuration_albert': {'AlbertConfig'}
            },
            frozenset({'tokenizers'}): {
                'tokenization_albert_fast': {'AlbertTokenizer'}
            },
        },
        'align': {
            frozenset(): {
                'configuration_align': {'AlignConfig', 'AlignTextConfig', 'AlignVisionConfig'},
                'processing_align': {'AlignProcessor'}
            },
        },
        'altclip': {
            frozenset(): {
                'configuration_altclip': {'AltCLIPConfig', 'AltCLIPTextConfig', 'AltCLIPVisionConfig'},
                'processing_altclip': {'AltCLIPProcessor'},
            }
        }
    }
    """
    import_structure = {}

    if os.path.isfile(module_path):
        module_path = os.path.dirname(module_path)

    adjacent_modules = []

    with os.scandir(module_path) as entries:
        for entry in entries:
            if entry.name == "__pycache__":
                continue
            if entry.is_dir():
                import_structure[entry.name] = create_import_structure_from_path(entry.path)
            elif not entry.name.startswith(("convert_", "modular_")):
                adjacent_modules.append(entry.name)

    # We're only taking a look at files different from __init__.py
    # We could theoretically require things directly from the __init__.py
    # files, but this is not supported at this time.
    if "__init__.py" in adjacent_modules:
        adjacent_modules.remove("__init__.py")

    module_requirements = {}
    for module_name in adjacent_modules:
        # Only modules ending in `.py` are accepted here.
        if not module_name.endswith(".py"):
            continue

        with open(os.path.join(module_path, module_name), encoding="utf-8") as f:
            file_content = f.read()

        # Remove the .py suffix
        module_name = module_name[:-3]

        previous_line = ""
        previous_index = 0

        # Some files have some requirements by default.
        # For example, any file named `modeling_xxx.py`
        # should have torch as a required backend.
        base_requirements = ()
        for check, requirements in BASE_FILE_REQUIREMENTS.items():
            if check(module_name, file_content):
                base_requirements = requirements
                break

        # Objects that have a `@require` assigned to them will get exported
        # with the backends specified in the decorator as well as the file backends.
        exported_objects = set()
        if "@requires" in file_content:
            lines = file_content.split("\n")
            for index, line in enumerate(lines):
                # This allows exporting items with other decorators. We'll take a look
                # at the line that follows at the same indentation level.
                if line.startswith((" ", "\t", "@", ")")) and not line.startswith("@requires"):
                    continue

                # Skipping line enables putting whatever we want between the
                # requires() call and the actual class/method definition.
                # This is what enables having # Copied from statements, docs, etc.
                skip_line = False

                if "@requires" in previous_line:
                    skip_line = False

                    # Backends are defined on the same line as requires
                    if "backends" in previous_line:
                        try:
                            backends_string = previous_line.split("backends=")[1].split("(")[1].split(")")[0]
                        except IndexError:
                            raise ValueError(
                                f"Couldn't parse backends for @requires decorator in file {module_name}:{previous_line}"
                            )
                        backends = tuple(sorted([b.strip("'\",") for b in backends_string.split(", ") if b]))

                    # Backends are defined in the lines following requires, for example such as:
                    # @requires(
                    #     backends=(
                    #             "sentencepiece",
                    #             "torch",
                    #     )
                    # )
                    #
                    # or
                    #
                    # @requires(
                    #     backends=(
                    #             "sentencepiece",
                    #     )
                    # )
                    elif "backends" in lines[previous_index + 1]:
                        backends = []
                        for backend_line in lines[previous_index:index]:
                            if "backends" in backend_line:
                                backend_line = backend_line.split("=")[1]
                            if '"' in backend_line or "'" in backend_line:
                                if ", " in backend_line:
                                    backends.extend(backend.strip("()\"', ") for backend in backend_line.split(", "))
                                else:
                                    backends.append(backend_line.strip("()\"', "))

                            # If the line is only a ')', then we reached the end of the backends and we break.
                            if backend_line.strip() == ")":
                                break
                        backends = tuple(backends)

                    # No backends are registered for requires
                    else:
                        backends = ()

                    backends = frozenset(backends + base_requirements)
                    if backends not in module_requirements:
                        module_requirements[backends] = {}
                    if module_name not in module_requirements[backends]:
                        module_requirements[backends][module_name] = set()

                    if not line.startswith("class") and not line.startswith("def"):
                        skip_line = True
                    else:
                        start_index = 6 if line.startswith("class") else 4
                        object_name = line[start_index:].split("(")[0].strip(":")
                        module_requirements[backends][module_name].add(object_name)
                        exported_objects.add(object_name)

                if not skip_line:
                    previous_line = line
                    previous_index = index

        # All objects that are in __all__ should be exported by default.
        # These objects are exported with the file backends.
        if "__all__" in file_content:
            for _all_object in fetch__all__(file_content):
                if _all_object not in exported_objects:
                    backends = frozenset(base_requirements)
                    if backends not in module_requirements:
                        module_requirements[backends] = {}
                    if module_name not in module_requirements[backends]:
                        module_requirements[backends][module_name] = set()

                    module_requirements[backends][module_name].add(_all_object)

    import_structure = {**module_requirements, **import_structure}
    return import_structure