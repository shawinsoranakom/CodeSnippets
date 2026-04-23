def parse_classes(self, node: ast.ClassDef) -> None:
        """Extracts "classes" from the code, including inheritance and init methods."""
        bases = self.get_base_classes()
        nodes = []
        for base in bases:
            if base.__name__ == node.name or base.__name__ in {"CustomComponent", "Component", "BaseComponent"}:
                continue
            try:
                class_node, import_nodes = find_class_ast_node(base)
                if class_node is None:
                    continue
                for import_node in import_nodes:
                    self.parse_imports(import_node)
                nodes.append(class_node)
            except Exception:  # noqa: BLE001
                logger.exception("Error finding base class node")
        nodes.insert(0, node)
        class_details = ClassCodeDetails(
            name=node.name,
            doc=ast.get_docstring(node),
            bases=[b.__name__ for b in bases],
            attributes=[],
            methods=[],
            init=None,
        )
        for _node in nodes:
            self.process_class_node(_node, class_details)
        self.data["classes"].append(class_details.model_dump())