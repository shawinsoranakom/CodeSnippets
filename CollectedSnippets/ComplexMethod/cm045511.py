def generate_toctree_from_rst_files(reference_dir: Path) -> Dict[str, List[str]]:
    """Generate toctree entries directly from existing .rst files."""
    # Initialize sections using constants
    toctree_sections: Dict[str, List[str]] = {section: [] for section in PACKAGE_SECTIONS.values()}

    python_ref_dir = reference_dir / "python"
    if not python_ref_dir.exists():
        return toctree_sections

    # Collect modules by package using constants
    modules_by_section: Dict[str, List[str]] = {section: [] for section in PACKAGE_SECTIONS.values()}

    # Get all .rst files and organize them by package
    for rst_file in python_ref_dir.glob("*.rst"):
        module_name = rst_file.stem  # filename without .rst extension

        # Find which documented package this module belongs to
        for package_prefix, section_name in PACKAGE_SECTIONS.items():
            if module_name.startswith(package_prefix):
                modules_by_section[section_name].append(module_name)
                break

    # Sort modules so parent modules come before child modules
    def sort_modules_hierarchically(modules):
        """Sort modules so that parent modules come before child modules."""
        return sorted(modules, key=lambda x: (x.count('.'), x))

    # Apply hierarchical sorting and convert to rst paths
    for section_name, modules in modules_by_section.items():
        toctree_sections[section_name] = [f"python/{m}" for m in sort_modules_hierarchically(modules)]

    return toctree_sections