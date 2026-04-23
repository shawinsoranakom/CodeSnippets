def add_pipeline_model_mapping(test_class, overwrite=False):
    """Add `pipeline_model_mapping` to `test_class`."""
    if getattr(test_class, "pipeline_model_mapping", None) is not None:
        if not overwrite:
            return "", -1

    line_to_add = get_pipeline_model_mapping_string(test_class)
    if len(line_to_add) == 0:
        return "", -1
    line_to_add = line_to_add + "\n"

    # The code defined the class `test_class`
    class_lines, class_start_line_no = inspect.getsourcelines(test_class)
    # `inspect` gives the code for an object, including decorator(s) if any.
    # We (only) need the exact line of the class definition.
    for idx, line in enumerate(class_lines):
        if line.lstrip().startswith("class "):
            class_lines = class_lines[idx:]
            class_start_line_no += idx
            break
    class_end_line_no = class_start_line_no + len(class_lines) - 1

    # The index in `class_lines` that starts the definition of `all_model_classes`, `all_generative_model_classes` or
    # `pipeline_model_mapping`. This assumes they are defined in such order, and we take the start index of the last
    # block that appears in a `test_class`.
    start_idx = None
    # The indent level of the line at `class_lines[start_idx]` (if defined)
    indent_level = 0
    # To record if `pipeline_model_mapping` is found in `test_class`.
    def_line = None
    for idx, line in enumerate(class_lines):
        if line.strip().startswith("all_model_classes = "):
            indent_level = len(line) - len(line.lstrip())
            start_idx = idx
        elif line.strip().startswith("all_generative_model_classes = "):
            indent_level = len(line) - len(line.lstrip())
            start_idx = idx
        elif line.strip().startswith("pipeline_model_mapping = "):
            indent_level = len(line) - len(line.lstrip())
            start_idx = idx
            def_line = line
            break

    if start_idx is None:
        return "", -1
    # Find the ending index (inclusive) of the above found block.
    end_idx = find_block_ending(class_lines, start_idx, indent_level)

    # Extract `is_xxx_available()` from existing blocks: some models require specific libraries like `timm` and use
    # `is_timm_available()` instead of `is_torch_available()`.
    # Keep leading and trailing whitespaces
    r = re.compile(r"\s(is_\S+?_available\(\))\s")
    for line in class_lines[start_idx : end_idx + 1]:
        backend_condition = r.search(line)
        if backend_condition is not None:
            # replace the leading and trailing whitespaces to the space character " ".
            target = " " + backend_condition[0][1:-1] + " "
            line_to_add = r.sub(target, line_to_add)
            break

    if def_line is None:
        # `pipeline_model_mapping` is not defined. The target index is set to the ending index (inclusive) of
        # `all_model_classes` or `all_generative_model_classes`.
        target_idx = end_idx
    else:
        # `pipeline_model_mapping` is defined. The target index is set to be one **BEFORE** its start index.
        target_idx = start_idx - 1
        # mark the lines of the currently existing `pipeline_model_mapping` to be removed.
        for idx in range(start_idx, end_idx + 1):
            # These lines are going to be removed before writing to the test file.
            class_lines[idx] = None  # noqa

    # Make sure the test class is a subclass of `PipelineTesterMixin`.
    parent_classes = [x.__name__ for x in test_class.__bases__]
    if "PipelineTesterMixin" not in parent_classes:
        # Put `PipelineTesterMixin` just before `unittest.TestCase`
        _parent_classes = [x for x in parent_classes if x != "TestCase"] + ["PipelineTesterMixin"]
        if "TestCase" in parent_classes:
            # Here we **assume** the original string is always with `unittest.TestCase`.
            _parent_classes.append("unittest.TestCase")
        parent_classes = ", ".join(_parent_classes)
        for idx, line in enumerate(class_lines):
            # Find the ending of the declaration of `test_class`
            if line.strip().endswith("):"):
                # mark the lines of the declaration of `test_class` to be removed
                for _idx in range(idx + 1):
                    class_lines[_idx] = None  # noqa
                break
        # Add the new, one-line, class declaration for `test_class`
        class_lines[0] = f"class {test_class.__name__}({parent_classes}):\n"

    # Add indentation
    line_to_add = " " * indent_level + line_to_add
    # Insert `pipeline_model_mapping` to `class_lines`.
    # (The line at `target_idx` should be kept by definition!)
    class_lines = class_lines[: target_idx + 1] + [line_to_add] + class_lines[target_idx + 1 :]
    # Remove the lines that are marked to be removed
    class_lines = [x for x in class_lines if x is not None]

    # Move from test class to module (in order to write to the test file)
    module_lines = inspect.getsourcelines(inspect.getmodule(test_class))[0]
    # Be careful with the 1-off between line numbers and array indices
    module_lines = module_lines[: class_start_line_no - 1] + class_lines + module_lines[class_end_line_no:]
    code = "".join(module_lines)

    moddule_file = inspect.getsourcefile(test_class)
    with open(moddule_file, "w", encoding="UTF-8", newline="\n") as fp:
        fp.write(code)

    return line_to_add