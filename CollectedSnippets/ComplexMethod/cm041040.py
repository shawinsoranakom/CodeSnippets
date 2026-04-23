def _setup_change_set_model(
        cls,
        change_set: ChangeSet,
        before_template: dict | None,
        after_template: dict | None,
        before_parameters: dict | None,
        after_parameters: dict | None,
        previous_update_model: UpdateModel | None = None,
    ):
        resolved_parameters = None
        if after_parameters is not None:
            resolved_parameters = cls._resolve_parameters(
                after_template,
                after_parameters,
                change_set.stack.account_id,
                change_set.stack.region_name,
                before_parameters,
            )

        change_set.resolved_parameters = resolved_parameters

        # Create and preprocess the update graph for this template update.
        change_set_model = ChangeSetModel(
            before_template=before_template,
            after_template=after_template,
            before_parameters=before_parameters,
            after_parameters=resolved_parameters,
        )
        raw_update_model: UpdateModel = change_set_model.get_update_model()
        # If there exists an update model which operated in the 'before' version of this change set,
        # port the runtime values computed for the before version into this latest update model.
        if previous_update_model:
            raw_update_model.before_runtime_cache.clear()
            raw_update_model.before_runtime_cache.update(previous_update_model.after_runtime_cache)
        change_set.set_update_model(raw_update_model)

        # Apply global transforms.
        # TODO: skip this process iff both versions of the template don't specify transform blocks.
        change_set_model_transform = ChangeSetModelTransform(
            change_set=change_set,
            before_parameters=before_parameters,
            after_parameters=resolved_parameters,
            before_template=before_template,
            after_template=after_template,
        )
        try:
            transformed_before_template, transformed_after_template = (
                change_set_model_transform.transform()
            )
        except FailedTransformationException as e:
            change_set.status = ChangeSetStatus.FAILED
            change_set.status_reason = e.message
            change_set.stack.set_stack_status(
                status=StackStatus.ROLLBACK_IN_PROGRESS, reason=e.message
            )
            change_set.stack.set_stack_status(status=StackStatus.CREATE_FAILED)
            return

        # Remodel the update graph after the applying the global transforms.
        change_set_model = ChangeSetModel(
            before_template=transformed_before_template,
            after_template=transformed_after_template,
            before_parameters=before_parameters,
            after_parameters=resolved_parameters,
        )
        update_model = change_set_model.get_update_model()
        # Bring the cache for the previous operations forward in the update graph for this version
        # of the templates. This enables downstream update graph visitors to access runtime
        # information computed whilst evaluating the previous version of this template, and during
        # the transformations.
        update_model.before_runtime_cache.update(raw_update_model.before_runtime_cache)
        update_model.after_runtime_cache.update(raw_update_model.after_runtime_cache)
        change_set.set_update_model(update_model)

        # perform validations
        validator = ChangeSetModelValidator(
            change_set=change_set,
        )
        validator.validate()

        # hacky
        if transform := raw_update_model.node_template.transform:
            if transform.global_transforms:
                # global transforms should always be considered "MODIFIED"
                update_model.node_template.change_type = ChangeType.MODIFIED
        change_set.processed_template = transformed_after_template

        if not config.CFN_IGNORE_UNSUPPORTED_RESOURCE_TYPES:
            support_visitor = ChangeSetResourceSupportChecker(
                change_set_type=change_set.change_set_type
            )
            support_visitor.visit(change_set.update_model.node_template)
            failure_messages = support_visitor.failure_messages
            if failure_messages:
                reason_suffix = ", ".join(failure_messages)
                status_reason = f"{ChangeSetResourceSupportChecker.TITLE_MESSAGE} {reason_suffix}"

                change_set.status_reason = status_reason
                change_set.set_change_set_status(ChangeSetStatus.FAILED)
                failure_transitions = {
                    ChangeSetType.CREATE: (
                        StackStatus.ROLLBACK_IN_PROGRESS,
                        StackStatus.CREATE_FAILED,
                    ),
                    ChangeSetType.UPDATE: (
                        StackStatus.UPDATE_ROLLBACK_IN_PROGRESS,
                        StackStatus.UPDATE_ROLLBACK_FAILED,
                    ),
                    ChangeSetType.IMPORT: (
                        StackStatus.IMPORT_ROLLBACK_IN_PROGRESS,
                        StackStatus.IMPORT_ROLLBACK_FAILED,
                    ),
                }
                transitions = failure_transitions.get(change_set.change_set_type)
                if transitions:
                    first_status, *remaining_statuses = transitions
                    change_set.stack.set_stack_status(first_status, status_reason)
                    for status in remaining_statuses:
                        change_set.stack.set_stack_status(status)
                return