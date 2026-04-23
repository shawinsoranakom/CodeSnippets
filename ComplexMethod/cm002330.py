def build_video_processor_mapping(
    config_mapping: dict[str, str],
) -> OrderedDict[str, dict[str, str | None]]:
    processor_mapping = OrderedDict()
    for model_type in config_mapping:
        module = model_type.replace("-", "_")
        video_processor_name = None

        if os.path.exists(f"src/transformers/models/{module}/video_processing_{module}.py"):
            with open(f"src/transformers/models/{module}/video_processing_{module}.py", "r") as f:
                content = f.read()

            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and any(
                    base.id == "BaseVideoProcessor" for base in node.bases if isinstance(base, ast.Name)
                ):
                    video_processor_name = node.name

        if video_processor_name is not None:
            processor_mapping[model_type] = video_processor_name

    return processor_mapping