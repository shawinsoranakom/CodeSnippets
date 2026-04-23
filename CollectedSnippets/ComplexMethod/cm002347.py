def visit_SimpleStatementLine(self, node):
        """If we visit an import statement not previously visited, record it. If we visit a module-scope assignment,
        simply record it or, if it is `__all__`, split it between files where we should dispatch it.
        """
        parent_node = self.get_metadata(cst.metadata.ParentNodeProvider, node)
        simple_top_level_assign_structure = m.SimpleStatementLine(
            body=[m.Assign(targets=[m.AssignTarget(target=m.Name())])]
        )
        simple_top_level_variable_indexing = m.SimpleStatementLine(
            body=[m.Assign(targets=[m.AssignTarget(target=m.Subscript(value=m.Name()) | m.Attribute(value=m.Name()))])]
        )

        if m.matches(parent_node, m.Module()):
            if m.matches(node, m.SimpleStatementLine(body=[m.Import()])):
                self.imports.append(node)
            elif m.matches(node, m.SimpleStatementLine(body=[m.ImportFrom()])):
                # `node.body[0].module` is None for fully relative imports, e.g. `from ... import initialization as init`
                import_module = (
                    self.python_module.code_for_node(node.body[0].module) if node.body[0].module is not None else ""
                )
                import_statement = "." * len(node.body[0].relative) + import_module
                if any(
                    external_file["name"] in import_statement for external_file in self.excluded_external_files
                ) or not (
                    re.search(rf"(?:transformers\.models\.)|(?:\.\.)\w+\.({self.match_patterns}).*", import_statement)
                    and not any(import_to_skip in import_statement for import_to_skip in IMPORTS_TO_SKIP_IN_MODULAR)
                ):
                    self.imports.append(node)
            elif m.matches(node, simple_top_level_assign_structure):
                assigned_variable = node.body[0].targets[0].target.value
                # __all__ is treated differently and not added to general assignments
                if assigned_variable == "__all__":
                    self.all_all_to_add = split_all_assignment(node, self.model_name)
                else:
                    self.current_assignment = assigned_variable
                    self.assignments[assigned_variable] = node
            # This corresponds to a global variable being indexed or having an attribute look-up
            elif m.matches(node, simple_top_level_variable_indexing):
                indexed_variable = node.body[0].targets[0].target.value.value
                # We should follow any dependencies relative to the variable being indexed
                self.current_assignment = indexed_variable
                # The indexing node should be directly added as a dependency of the indexed variable (register the node with a "fake" name)
                node_name = self.python_module.code_for_node(node)
                self.assignments[node_name] = node
                self.object_dependency_mapping[indexed_variable].add(node_name)