def test_takes_context_without_taking_context(self):
        with self.assertRaisesMessage(
            InvalidTask,
            "Task takes context but does not have a first argument of 'context'.",
        ):
            task(takes_context=True)(test_tasks.calculate_meaning_of_life.func)