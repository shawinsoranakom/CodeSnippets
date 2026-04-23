def merge_model_specific_imports(self, visited_modules):
        """Merge the functions and assignments imported from the modeling files to the modular nodes and dependency graph,
        based on the visited files."""
        self.start_lines_file_mapping = {}
        self.added_objects_file_mapping = {}
        for object_name, file in self.model_specific_imported_objects.items():
            visited_module = visited_modules[file]
            self.start_lines_file_mapping[file] = visited_module.start_lines
            # Add functions and their dependencies
            if object_name in visited_module.functions and object_name not in self.functions:
                self.functions[object_name] = visited_module.functions[object_name]
                self.added_objects_file_mapping[object_name] = file
                dependencies = visited_module.object_dependency_mapping.get(object_name, None)
                if dependencies is not None:
                    self.object_dependency_mapping[object_name] = dependencies
                    for dep in dependencies:
                        if dep not in self.global_nodes:
                            self.added_objects_file_mapping[dep] = file
                            self.functions[dep] = visited_module.global_nodes[dep]

                # Add/overwrite the imported functions to other visited modules as well, in case it is absent/different
                # in the modeling source file of the inherited class. See `examples/modular-tranformers/modular_switch_function.py`
                # and `examples/modular-tranformers/modular_add_function.py` for examples
                recursive_dependencies = visited_module.object_recursive_dependency_mapping.get(object_name, set())
                node_recursive_dependencies_mapping = {
                    dep: visited_module.global_nodes[dep] for dep in recursive_dependencies
                }
                for filename, module_mapper in self.visited_modules.items():
                    if filename != file:
                        module_mapper.global_nodes[object_name] = visited_module.functions[object_name]
                        if len(recursive_dependencies) > 0:
                            module_mapper.object_recursive_dependency_mapping[object_name] = recursive_dependencies
                            module_mapper.global_nodes.update(node_recursive_dependencies_mapping)

            # Add assignments and their dependencies
            elif object_name in visited_module.assignments and object_name not in self.assignments:
                self.assignments[object_name] = visited_module.assignments[object_name]
                self.added_objects_file_mapping[object_name] = file
                dependencies = visited_module.object_dependency_mapping.get(object_name, None)
                if dependencies is not None:
                    self.object_dependency_mapping[object_name] = dependencies
                    for dep in dependencies:
                        if dep not in self.global_nodes:
                            self.added_objects_file_mapping[dep] = file
                            self.assignments[dep] = visited_module.global_nodes[dep]

        # Do not forget to re-assign all nodes after the merge
        self.global_nodes = {**self.assignments, **self.classes, **self.functions}
        # And restric dependencies to those nodes only
        self._restrict_dependencies_to_known_entities()