async def async_step_init(self, user_input=None):
            if user_input and "task_finished" in user_input:
                if user_input["task_finished"] == 1:
                    self.task_one_done = True
                elif user_input["task_finished"] == 2:
                    self.task_two_done = True

            if not self.task_one_done:
                progress_action = "task_one"
            elif not self.task_two_done:
                progress_action = "task_two"
            if not self.task_one_done or not self.task_two_done:
                return self.async_show_progress(
                    step_id="init",
                    progress_action=progress_action,
                )

            self.data = user_input
            return self.async_show_progress_done(next_step_id="finish")