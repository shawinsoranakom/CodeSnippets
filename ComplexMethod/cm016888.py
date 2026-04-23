def extract_node_configuration(path) -> Optional[PyProjectConfig]:
    if os.path.isfile(path):
        file_path = Path(path)

        if file_path.suffix.lower() != '.py':
            return None

        project_name = file_path.stem
        project = ProjectConfig(name=project_name)
        comfy = ComfyConfig()
        return PyProjectConfig(project=project, tool_comfy=comfy)

    folder_name = os.path.basename(path)
    toml_path = Path(path) / "pyproject.toml"

    if not toml_path.exists():
        project = ProjectConfig(name=folder_name)
        comfy = ComfyConfig()
        return PyProjectConfig(project=project, tool_comfy=comfy)

    raw_settings = load_pyproject_settings(toml_path)

    project_data = raw_settings.project

    tool_data = raw_settings.tool
    comfy_data = tool_data.get("comfy", {}) if tool_data else {}

    dependencies = project_data.get("dependencies", [])
    supported_comfyui_frontend_version = ""
    for dep in dependencies:
        if isinstance(dep, str) and dep.startswith("comfyui-frontend-package"):
            supported_comfyui_frontend_version = dep.removeprefix("comfyui-frontend-package")
            break

    supported_comfyui_version = comfy_data.get("requires-comfyui", "")

    classifiers = project_data.get('classifiers', [])
    supported_os = validate_and_extract_os_classifiers(classifiers)
    supported_accelerators = validate_and_extract_accelerator_classifiers(classifiers)

    project_data['supported_os'] = supported_os
    project_data['supported_accelerators'] = supported_accelerators
    project_data['supported_comfyui_frontend_version'] = supported_comfyui_frontend_version
    project_data['supported_comfyui_version'] = supported_comfyui_version

    return PyProjectConfig(project=project_data, tool_comfy=comfy_data)