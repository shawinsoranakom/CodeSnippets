def build_file_tree(file_stats: List[FileStats]) -> Dict[str, TreeNode]:
        """Build hierarchical tree grouped by module type, then by module structure.

        Args:
            file_stats: List of FileStats objects

        Returns:
            Dictionary mapping module types to their tree roots
        """
        # Group by module type first
        type_groups = {'stdlib': [], 'site-packages': [], 'project': [], 'other': []}
        for stat in file_stats:
            type_groups[stat.module_type].append(stat)

        # Build tree for each type
        trees = {}
        for module_type, stats in type_groups.items():
            if not stats:
                continue

            root_node = TreeNode()

            for stat in stats:
                module_name = stat.module_name
                parts = module_name.split('.')

                # Navigate/create tree structure
                current_node = root_node
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # Last part - store the file
                        current_node.files.append(stat)
                    else:
                        # Intermediate part - create or navigate
                        if part not in current_node.children:
                            current_node.children[part] = TreeNode()
                        current_node = current_node.children[part]

            # Calculate aggregate stats for this type's tree
            _TreeBuilder._calculate_node_stats(root_node)
            trees[module_type] = root_node

        return trees