def check_call(self, node: astroid.nodes.Call, name: str, args: tuple[str, ...]) -> None:
        """Check the given deprecation call node for valid arguments."""
        call_args = self.get_deprecation_call_args(node, args)

        self.check_collection_name(node, name, call_args)

        if not call_args.version and not call_args.date:
            self.add_message('ansible-deprecated-no-version', node=node, args=(name,))
            return

        if call_args.date and self.is_ansible_core:
            self.add_message('ansible-deprecated-date-not-permitted', node=node, args=(name,))
            return

        if call_args.all_args_dynamic():
            # assume collection maintainers know what they're doing if all args are dynamic
            return

        if call_args.version and call_args.date:
            self.add_message('ansible-deprecated-both-version-and-date', node=node, args=(name,))
            return

        if call_args.date:
            self.check_date(node, name, call_args)

        if call_args.version:
            self.check_version(node, name, call_args)