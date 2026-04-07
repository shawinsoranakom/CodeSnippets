def test_invalid_priority(self):
        with self.assertRaisesMessage(
            InvalidTask,
            f"priority must be a whole number between {TASK_MIN_PRIORITY} and "
            f"{TASK_MAX_PRIORITY}.",
        ):
            test_tasks.noop_task.using(priority=-101)

        with self.assertRaisesMessage(
            InvalidTask,
            f"priority must be a whole number between {TASK_MIN_PRIORITY} and "
            f"{TASK_MAX_PRIORITY}.",
        ):
            test_tasks.noop_task.using(priority=101)

        with self.assertRaisesMessage(
            InvalidTask,
            f"priority must be a whole number between {TASK_MIN_PRIORITY} and "
            f"{TASK_MAX_PRIORITY}.",
        ):
            test_tasks.noop_task.using(priority=3.1)

        test_tasks.noop_task.using(priority=100)
        test_tasks.noop_task.using(priority=-100)
        test_tasks.noop_task.using(priority=0)