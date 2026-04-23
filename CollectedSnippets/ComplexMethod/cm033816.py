def check_collection_version(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the collection version provided to the given call node."""
        try:
            if not isinstance(args.version, str) or not args.version:
                raise ValueError()

            semantic_version = SemanticVersion(args.version)
        except ValueError:
            self.add_message('collection-invalid-deprecated-version', node=node, args=(args.version, name))
            return

        if self.collection_version >= semantic_version:
            self.add_message('collection-deprecated-version', node=node, args=(args.version, name))

        if semantic_version.major != 0 and (semantic_version.minor != 0 or semantic_version.patch != 0):
            self.add_message('removal-version-must-be-major', node=node, args=(args.version,))