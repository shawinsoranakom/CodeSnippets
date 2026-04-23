def build_config_mapping_names() -> tuple[dict, dict]:
    model_type_map = OrderedDict()
    special_mappings = OrderedDict()

    # root_path = Path(__file__).resolve().parents[2]
    all_files = glob.glob("src/transformers/models/**/configuration_*.py", recursive=True)
    for config_path in all_files:
        module_name = config_path.split("/")[-2]
        with open(config_path, "r") as f:
            content = f.read()

        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(
                base.id == "PreTrainedConfig" for base in node.bases if isinstance(base, ast.Name)
            ):
                config_cls_name = node.name
                model_type = None
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        if model_types := [
                            stmt.value.value
                            for target in stmt.targets
                            if isinstance(target, ast.Name) and target.id == "model_type"
                        ]:
                            model_type = model_types[0]
                            break
                    elif isinstance(stmt, ast.AnnAssign):
                        if stmt.target.id == "model_type":
                            model_type = stmt.value.value
                            break

                if not model_type:
                    continue

                if model_type != module_name:
                    special_mappings[model_type] = module_name
                model_type_map[model_type] = config_cls_name

    return model_type_map, special_mappings