def construct_changes(
        self,
        existing_stack,
        new_stack,
        # TODO: remove initialize argument from here, and determine action based on resource status
        initialize: bool | None = False,
        change_set_id=None,
        append_to_changeset: bool | None = False,
        filter_unchanged_resources: bool | None = False,
    ) -> list[ChangeConfig]:
        old_resources = existing_stack.template["Resources"]
        new_resources = new_stack.template["Resources"]
        deletes = [val for key, val in old_resources.items() if key not in new_resources]
        adds = [val for key, val in new_resources.items() if initialize or key not in old_resources]
        modifies = [
            val for key, val in new_resources.items() if not initialize and key in old_resources
        ]

        changes = []
        for action, items in (("Remove", deletes), ("Add", adds), ("Modify", modifies)):
            for item in items:
                item["Properties"] = item.get("Properties", {})
                if (
                    not filter_unchanged_resources  # TODO: find out purpose of this
                    or action != "Modify"
                    or self.resource_config_differs(item)
                ):
                    change = self.get_change_config(action, item, change_set_id=change_set_id)
                    changes.append(change)

        # append changes to change set
        if append_to_changeset and isinstance(new_stack, StackChangeSet):
            new_stack.changes.extend(changes)

        return changes