def check_models_have_kwargs():
    """
    Checks that all model classes defined in modeling files accept **kwargs in their forward pass.
    Since we ast.parse() here, it might be a good idea to add other tests that inspect modeling code here rather than
    repeatedly ast.parsing() in each test!
    """
    models_dir = Path(PATH_TO_TRANSFORMERS) / "models"
    failing_classes = []
    for model_dir in models_dir.iterdir():
        if model_dir.name == "deprecated":
            continue
        if model_dir.is_dir() and (modeling_file := list(model_dir.glob("modeling_*.py"))):
            modeling_file = modeling_file[0]

            with open(modeling_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            # Map all classes in the file to their base classes
            class_bases = {}
            all_class_nodes = {}

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    # We only care about base classes that are simple names
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    class_bases[node.name] = bases
                    all_class_nodes[node.name] = node

            inherits_from_pretrained = {"PreTrainedModel"}
            # Loop over classes and mark the ones that inherit from PreTrainedModel, or from
            # previously marked classes (which indicates indirect inheritance from PreTrainedModel)
            # Keep going until you go through the whole list without discovering a new child class, then break
            while True:
                for class_name, bases in class_bases.items():
                    if class_name in inherits_from_pretrained:
                        continue
                    if inherits_from_pretrained.intersection(bases):
                        inherits_from_pretrained.add(class_name)
                        break
                else:
                    break

            # 2. Iterate through classes and check conditions
            for class_name, class_def in all_class_nodes.items():
                if class_name not in inherits_from_pretrained:
                    continue

                forward_method = next(
                    (n for n in class_def.body if isinstance(n, ast.FunctionDef) and n.name == "forward"), None
                )
                if forward_method:
                    # 3. Check for **kwargs (represented as .kwarg in AST)
                    if forward_method.args.kwarg is None:
                        failing_classes.append(class_name)

    if failing_classes:
        raise Exception(
            "The following model classes do not accept **kwargs in their forward() method: \n"
            f"{', '.join(failing_classes)}."
        )