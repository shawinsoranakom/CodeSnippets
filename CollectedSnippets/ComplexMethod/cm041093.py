def execute(self) -> ChangeSetModelExecutorResult:
        # constructive process
        failure_message = None
        try:
            self.process()
        except TriggerRollback as e:
            failure_message = e.reason
        except Exception as e:
            failure_message = str(e)

        is_deletion = self._change_set.stack.status == StackStatus.DELETE_IN_PROGRESS
        if self._deferred_actions:
            if not is_deletion:
                # TODO: correct status
                # TODO: differentiate between update and create
                self._change_set.stack.set_stack_status(
                    StackStatus.ROLLBACK_IN_PROGRESS
                    if failure_message
                    else StackStatus.UPDATE_COMPLETE_CLEANUP_IN_PROGRESS
                )

            # perform all deferred actions such as deletions. These must happen in reverse from their
            # defined order so that resource dependencies are honoured
            # TODO: errors will stop all rollbacks; get parity on this behaviour
            for deferred in self._deferred_actions[::-1]:
                LOG.debug("executing deferred action: '%s'", deferred.name)
                deferred.action()

        if failure_message and not is_deletion:
            # TODO: differentiate between update and create
            self._change_set.stack.set_stack_status(StackStatus.ROLLBACK_COMPLETE)

        return ChangeSetModelExecutorResult(
            resources=self.resources, outputs=self.outputs, failure_message=failure_message
        )