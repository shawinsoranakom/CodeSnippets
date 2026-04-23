def do_apply_changes_in_loop(self, changes: list[ChangeConfig], stack: Stack) -> list:
        # apply changes in a retry loop, to resolve resource dependencies and converge to the target state
        changes_done = []
        new_resources = stack.resources

        sorted_changes = order_changes(
            given_changes=changes,
            resources=new_resources,
            resolved_conditions=stack.resolved_conditions,
            resolved_parameters=stack.resolved_parameters,
        )
        for change_idx, change in enumerate(sorted_changes):
            res_change = change["ResourceChange"]
            action = res_change["Action"]
            is_add_or_modify = action in ["Add", "Modify"]
            resource_id = res_change["LogicalResourceId"]

            # TODO: do resolve_refs_recursively once here
            try:
                if is_add_or_modify:
                    should_deploy = self.prepare_should_deploy_change(
                        resource_id, change, stack, new_resources
                    )
                    LOG.debug(
                        'Handling "%s" for resource "%s" (%s/%s) type "%s" (should_deploy=%s)',
                        action,
                        resource_id,
                        change_idx + 1,
                        len(changes),
                        res_change["ResourceType"],
                        should_deploy,
                    )
                    if not should_deploy:
                        stack_action = get_action_name_for_resource_change(action)
                        stack.set_resource_status(resource_id, f"{stack_action}_COMPLETE")
                        continue
                elif action == "Remove":
                    should_remove = self.prepare_should_deploy_change(
                        resource_id, change, stack, new_resources
                    )
                    if not should_remove:
                        continue
                    LOG.debug(
                        'Handling "%s" for resource "%s" (%s/%s) type "%s"',
                        action,
                        resource_id,
                        change_idx + 1,
                        len(changes),
                        res_change["ResourceType"],
                    )
                self.apply_change(change, stack=stack)
                changes_done.append(change)
            except Exception as e:
                status_action = {
                    "Add": "CREATE",
                    "Modify": "UPDATE",
                    "Dynamic": "UPDATE",
                    "Remove": "DELETE",
                }[action]
                stack.add_stack_event(
                    resource_id=resource_id,
                    physical_res_id=new_resources[resource_id].get("PhysicalResourceId"),
                    status=f"{status_action}_FAILED",
                    status_reason=str(e),
                )
                if config.CFN_VERBOSE_ERRORS:
                    LOG.exception("Failed to deploy resource %s, stack deploy failed", resource_id)
                raise

        # clean up references to deleted resources in stack
        deletes = [c for c in changes_done if c["ResourceChange"]["Action"] == "Remove"]
        for delete in deletes:
            stack.template["Resources"].pop(delete["ResourceChange"]["LogicalResourceId"], None)

        # resolve outputs
        stack.resolved_outputs = resolve_outputs(self.account_id, self.region_name, stack)

        return changes_done