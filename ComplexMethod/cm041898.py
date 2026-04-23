def extract_class_and_function_info(self, tree, file_path) -> RepoFileInfo:
        """
        Extracts class, function, and global variable information from the Abstract Syntax Tree (AST).

        Args:
            tree: The Abstract Syntax Tree (AST) of the Python file.
            file_path: The path to the Python file.

        Returns:
            RepoFileInfo: A RepoFileInfo object containing the extracted information.
        """
        file_info = RepoFileInfo(file=str(file_path.relative_to(self.base_directory)))
        for node in tree:
            info = RepoParser.node_to_str(node)
            if info:
                file_info.page_info.append(info)
            if isinstance(node, ast.ClassDef):
                class_methods = [m.name for m in node.body if is_func(m)]
                file_info.classes.append({"name": node.name, "methods": class_methods})
            elif is_func(node):
                file_info.functions.append(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    if isinstance(target, ast.Name):
                        file_info.globals.append(target.id)
        return file_info