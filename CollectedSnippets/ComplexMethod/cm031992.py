def extract_chinese_characters(file_path):
        syntax = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            import ast
            root = ast.parse(content)
            for node in ast.walk(root):
                if isinstance(node, ast.Name):
                    if contains_chinese(node.id): syntax.append(node.id)
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if contains_chinese(n.name): syntax.append(n.name)
                elif isinstance(node, ast.ImportFrom):
                    for n in node.names:
                        if contains_chinese(n.name): syntax.append(n.name)
                        # if node.module is None: print(node.module)
                        for k in node.module.split('.'):
                            if contains_chinese(k): syntax.append(k)
            return syntax