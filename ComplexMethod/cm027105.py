def _process_one_task_or_event_or_recover(self, task: RecorderTask | Event) -> None:
        """Process a task or event, reconnect, or recover a malformed database."""
        try:
            # Almost everything coming in via the queue
            # is an Event so we can process it directly
            # and since its never subclassed, we can
            # use a fast type check
            if type(task) is Event:
                self._process_one_event(task)
                return
            # If its not an event, commit everything
            # that is pending before running the task
            if TYPE_CHECKING:
                assert isinstance(task, RecorderTask)
            if task.commit_before:
                self._commit_event_session_or_retry()
            task.run(self)
        except exc.DatabaseError as err:
            if self._handle_database_error(err, setup_run=True):
                return
            _LOGGER.exception("Unhandled database error while processing task %s", task)
        except SQLAlchemyError:
            _LOGGER.exception("SQLAlchemyError error processing task %s", task)
        else:
            return

        # Reset the session if an SQLAlchemyError (including DatabaseError)
        # happens to rollback and recover
        self._reopen_event_session()