def _module_match_label(module_name, label):
        # Exact or ancestor match.
        return module_name == label or module_name.startswith(label + ".")