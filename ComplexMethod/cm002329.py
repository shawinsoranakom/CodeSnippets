def build_image_processor_mapping(
    config_mapping: dict[str, str],
) -> OrderedDict[str, dict[str, str | None]]:
    processor_mapping = OrderedDict()
    for model_type in config_mapping:
        module = model_type.replace("-", "_")
        fast_processor_name = slow_processor_name = None
        if os.path.exists(f"src/transformers/models/{module}/image_processing_pil_{module}.py"):
            with open(f"src/transformers/models/{module}/image_processing_pil_{module}.py", "r") as f:
                content = f.read()

            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and any(
                    base.id == "PilBackend" for base in node.bases if isinstance(base, ast.Name)
                ):
                    slow_processor_name = node.name

        if os.path.exists(f"src/transformers/models/{module}/image_processing_{module}.py"):
            with open(f"src/transformers/models/{module}/image_processing_{module}.py", "r") as f:
                content = f.read()

            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and any(
                    base.id == "TorchvisionBackend" for base in node.bases if isinstance(base, ast.Name)
                ):
                    fast_processor_name = node.name

        if slow_processor_name is not None or fast_processor_name is not None:
            processor_mapping[model_type] = {
                **({"pil": slow_processor_name} if slow_processor_name else {}),
                **({"torchvision": fast_processor_name} if fast_processor_name else {}),
            }

    return processor_mapping