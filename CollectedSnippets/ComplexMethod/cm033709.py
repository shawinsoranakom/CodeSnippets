def _add_cobertura_package(packages: Element, package_name: str, package_data: dict[str, dict[str, int]]) -> tuple[int, int]:
    """Add a package element to the given packages element."""
    elem_package = SubElement(packages, 'package')
    elem_classes = SubElement(elem_package, 'classes')

    total_lines_hit = 0
    total_line_count = 0

    for path, results in package_data.items():
        lines_hit = len([True for hits in results.values() if hits])
        line_count = len(results)

        total_lines_hit += lines_hit
        total_line_count += line_count

        elem_class = SubElement(elem_classes, 'class')

        class_name = os.path.splitext(os.path.basename(path))[0]
        if class_name.startswith("Ansible.ModuleUtils"):
            class_name = class_name[20:]

        content_root = data_context().content.root
        filename = path
        if filename.startswith(content_root):
            filename = filename[len(content_root) + 1:]

        elem_class.attrib.update({
            'branch-rate': '0',
            'complexity': '0',
            'filename': filename,
            'line-rate': str(round(lines_hit / line_count, 4)) if line_count else "0",
            'name': class_name,
        })

        SubElement(elem_class, 'methods')

        elem_lines = SubElement(elem_class, 'lines')

        for number, hits in results.items():
            elem_line = SubElement(elem_lines, 'line')
            elem_line.attrib.update(
                hits=str(hits),
                number=str(number),
            )

    elem_package.attrib.update({
        'branch-rate': '0',
        'complexity': '0',
        'line-rate': str(round(total_lines_hit / total_line_count, 4)) if total_line_count else "0",
        'name': package_name,
    })

    return total_lines_hit, total_line_count