def create_todoist_task(self, data: Task):
        """Create a dictionary based on a Task passed from the Todoist API.

        Will return 'None' if the task is to be filtered out.
        """
        task: TodoistEvent = {
            ALL_DAY: False,
            COMPLETED: data.completed_at is not None,
            DESCRIPTION: f"https://todoist.com/showTask?id={data.id}",
            DUE_TODAY: False,
            END: None,
            LABELS: [],
            OVERDUE: False,
            PRIORITY: data.priority,
            START: dt_util.now(),
            SUMMARY: data.content,
        }

        if (
            self._project_id_whitelist
            and data.project_id not in self._project_id_whitelist
        ):
            # Project isn't in `include_projects` filter.
            return None

        # All task Labels (optional parameter).
        labels = data.labels or []
        task[LABELS] = [label.name for label in self._labels if label.name in labels]
        if self._label_whitelist and (
            not any(label in task[LABELS] for label in self._label_whitelist)
        ):
            # We're not on the whitelist, return invalid task.
            return None

        # Due dates (optional parameter).
        # The due date is the END date -- the task cannot be completed
        # past this time.
        # That means that the START date is the earliest time one can
        # complete the task.
        # Generally speaking, that means right now.
        if data.due is not None:
            due_date = data.due.date
            # The API returns date or datetime objects when deserialized via from_dict()
            if isinstance(due_date, datetime):
                task[END] = dt_util.as_local(due_date)
            elif isinstance(due_date, date):
                task[END] = dt_util.start_of_local_day(due_date)

            if (end_dt := task[END]) is not None:
                if self._due_date_days is not None:
                    # For comparison with now, use datetime

                    if end_dt > dt_util.now() + self._due_date_days:
                        # This task is out of range of our due date;
                        # it shouldn't be counted.
                        return None

                task[DUE_TODAY] = end_dt.date() == dt_util.now().date()

                # Special case: Task is overdue.
                if end_dt <= task[START]:
                    task[OVERDUE] = True
                    # Set end time to the current time plus 1 hour.
                    # We're pretty much guaranteed to update within that 1 hour,
                    # so it should be fine.
                    task[END] = task[START] + timedelta(hours=1)
                else:
                    task[OVERDUE] = False
        else:
            # If we ask for everything due before a certain date, don't count
            # things which have no due dates.
            if self._due_date_days is not None:
                return None

            # Define values for tasks without due dates
            task[END] = None
            task[ALL_DAY] = True
            task[DUE_TODAY] = False
            task[OVERDUE] = False

        # Not tracked: id, comments, project_id order, indent, recurring.
        return task