def check_collection_name(self, node: astroid.nodes.Call, name: str, args: DeprecationCallArgs) -> None:
        """Check the collection name provided to the given call node."""
        deprecator_requirement = self.is_deprecator_required()

        if self.is_ansible_core and args.collection_name:
            self.add_message('ansible-deprecated-collection-name-not-permitted', node=node, args=(name,))
            return

        if args.collection_name and args.deprecator:
            self.add_message('ansible-deprecated-both-collection-name-and-deprecator', node=node, args=(name,))

        if deprecator_requirement is True:
            if not args.collection_name and not args.deprecator:
                self.add_message('ansible-deprecated-no-collection-name', node=node, args=(name,))
                return
        elif deprecator_requirement is False:
            if args.collection_name:
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('collection_name', name,))
                return

            if args.deprecator:
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('deprecator', name,))
                return
        else:
            # collection_name may be needed for backward compat with 2.18 and earlier, since it is only detected in 2.19 and later

            if args.deprecator:
                # Unlike collection_name, which is needed for backward compat, deprecator is generally not needed by collections.
                # For the very rare cases where this is needed by collections, an inline pylint ignore can be used to silence it.
                self.add_message('ansible-deprecated-unnecessary-collection-name', node=node, args=('deprecator', name,))
                return

        if args.all_args_dynamic():
            # assume collection maintainers know what they're doing if all args are dynamic
            return

        expected_collection_name = 'ansible.builtin' if self.is_ansible_core else self.collection_name

        if args.collection_name and args.collection_name != expected_collection_name:
            self.add_message('wrong-collection-deprecated', node=node, args=(args.collection_name, name))