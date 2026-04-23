async def async_step_init(self, user_input=None):
            async def long_running_job_one() -> None:
                await task_one_evt.wait()

            async def long_running_job_two() -> None:
                self.async_update_progress(0.25)
                await task_two_evt.wait()
                self.async_update_progress(0.75)
                self.data = {"title": "Hello"}

            uncompleted_task: asyncio.Task[None] | None = None
            if not self.task_one:
                self.task_one = hass.async_create_task(long_running_job_one())

            progress_action = None
            if not self.task_one.done():
                progress_action = "task_one"
                uncompleted_task = self.task_one

            if not uncompleted_task:
                if not self.task_two:
                    self.task_two = hass.async_create_task(long_running_job_two())

                if not self.task_two.done():
                    progress_action = "task_two"
                    uncompleted_task = self.task_two

            if uncompleted_task:
                assert progress_action
                return self.async_show_progress(
                    progress_action=progress_action,
                    progress_task=uncompleted_task,
                )

            return self.async_show_progress_done(next_step_id="finish")