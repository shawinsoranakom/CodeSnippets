def _build_ast_indexes(source: str, tree: ast.Module | None = None) -> list[DecoratedItem]:
    """Parse source once and return list of all @auto_docstring decorated items.

    Returns:
        List of DecoratedItem objects, one for each @auto_docstring decorated function or class.
    """
    if tree is None:
        tree = ast.parse(source)
    # First pass: collect top-level string variables (for resolving custom_args variable references)
    var_to_string: dict[str, str] = {}
    for node in tree.body:
        # Handle: ARGS = "some string"
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_to_string[target.id] = node.value.value
        # Handle: ARGS: str = "some string"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str) and isinstance(node.target, ast.Name):
                var_to_string[node.target.id] = node.value.value
    # Second pass: find all @auto_docstring decorated functions/classes
    # First, identify processor classes to track method context (only top-level classes)
    processor_classes: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and ("ProcessorMixin" in base.id or "Processor" in base.id):
                    processor_classes.add(node.name)
                    break

    decorated_items: list[DecoratedItem] = []

    # Helper function to process decorated items
    def process_node(node, parent_class_name=None):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        # Find @auto_docstring decorator and extract custom_args if present
        decorator_line = None
        custom_args_text = None
        for dec in node.decorator_list:
            if not _is_auto_docstring_decorator(dec):
                continue
            decorator_line = dec.lineno
            # Extract custom_args from @auto_docstring(custom_args=...)
            if isinstance(dec, ast.Call):
                for kw in dec.keywords:
                    if kw.arg == "custom_args":
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            custom_args_text = kw.value.value.strip()
                        elif isinstance(kw.value, ast.Name):
                            custom_args_text = var_to_string.get(kw.value.id, "").strip()
            break
        if decorator_line is None:  # No @auto_docstring decorator found
            return
        # Extract info for this decorated item
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        body_start_line = node.body[0].lineno if node.body else node.lineno + 1
        # Extract function arguments (skip self, *args, **kwargs)
        arg_names = []
        has_init = False
        init_def_line = None
        is_model_output = False
        is_processor = False
        is_config = False

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # For functions/methods, extract args directly
            arg_names = _extract_function_args(node)
            # Check if this method is inside a processor class
            if parent_class_name and parent_class_name in processor_classes:
                is_processor = True
        elif isinstance(node, ast.ClassDef):
            # For classes, look for __init__ method and check if it's a ModelOutput or Processor
            # Check if class inherits from ModelOutput, ProcessorMixin, or PreTrainedConfig
            for base in node.bases:
                if isinstance(base, ast.Name):
                    if "ModelOutput" in base.id:
                        is_model_output = True
                    elif "ProcessorMixin" in base.id or "Processor" in base.id:
                        is_processor = True
                    elif base.id == "PreTrainedConfig":
                        is_config = True
            # Look for __init__ method in the class body
            for class_item in node.body:
                if isinstance(class_item, ast.FunctionDef) and class_item.name == "__init__":
                    has_init = True
                    init_def_line = class_item.lineno
                    arg_names = _extract_function_args(class_item)
                    # Update body_start_line to be the __init__ body start
                    body_start_line = class_item.body[0].lineno if class_item.body else class_item.lineno + 1
                    break
            # For config classes (PreTrainedConfig subclasses), extract class-level type annotations as args.
            # These use @strict from huggingface_hub which generates __init__ from annotations, so there is
            # no explicit __init__ in the source. The docstring and parameters live at the class body level.
            if is_config and not has_init:
                for class_item in node.body:
                    if isinstance(class_item, ast.AnnAssign) and isinstance(class_item.target, ast.Name):
                        attr_name = class_item.target.id
                        if attr_name.startswith("_"):
                            continue
                        # Skip ClassVar annotations (class-level metadata, not config parameters)
                        ann = class_item.annotation
                        if (
                            isinstance(ann, ast.Subscript)
                            and isinstance(ann.value, ast.Name)
                            and ann.value.id == "ClassVar"
                        ):
                            continue
                        arg_names.append(attr_name)

        decorated_items.append(
            DecoratedItem(
                decorator_line=decorator_line,
                def_line=node.lineno,
                kind=kind,
                body_start_line=body_start_line,
                args=arg_names,
                custom_args_text=custom_args_text,
                has_init=has_init,
                init_def_line=init_def_line,
                is_model_output=is_model_output,
                is_processor=is_processor,
                is_config=is_config,
                name=node.name,
                class_name=parent_class_name,
            )
        )

    # Traverse tree with parent context
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # Check class itself
            process_node(node)
            # Check methods within the class
            for class_item in node.body:
                process_node(class_item, parent_class_name=node.name)
        else:
            # Top-level functions
            process_node(node)

    return sorted(decorated_items, key=lambda x: x.decorator_line)