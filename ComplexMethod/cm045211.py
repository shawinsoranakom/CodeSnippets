async def _iterate_on_task(self, task: str, expected_answer: str) -> Tuple[str, None | str]:
        """
        Repeatedly assigns a task to the agent, and tries to learn from failures by creating useful insights as memories.
        """
        self.logger.enter_function()
        self.logger.info("\nTask description:  {}".format(task))
        self.logger.info("\nExpected answer:  {}\n".format(expected_answer))

        final_response = ""
        old_memos = await self.retrieve_relevant_memos(task)
        old_insights = [memo.insight for memo in old_memos]
        new_insights: List[str] = []
        last_insight = None
        insight = None
        successful_insight = None

        # Loop until success (or timeout) while learning from failures.
        for trial in range(1, self.max_train_trials + 1):
            self.logger.info("\n-----  TRAIN TRIAL {}  -----\n".format(trial))
            task_plus_insights = task

            # Add any new insights we've accumulated so far.
            if last_insight is not None:
                memory_section = self._format_memory_section(old_insights + [last_insight])
            else:
                memory_section = self._format_memory_section(old_insights)
            if len(memory_section) > 0:
                task_plus_insights += "\n\n" + memory_section

            # Can we find a failure case to learn from?
            failure_found, response, work_history = await self._test_for_failure(
                task, task_plus_insights, expected_answer
            )
            if not failure_found:
                # No. Time to exit the loop.
                self.logger.info("\nResponse is CORRECT.\n  Stop looking for insights.\n")
                # Was this the first trial?
                if trial == 1:
                    # Yes. We should return the successful response, and no insight.
                    final_response = response
                else:
                    # No. We learned a successful insight, which should be returned.
                    successful_insight = insight
                break

            # Will we try again?
            if trial == self.max_train_trials:
                # No. We're out of training trials.
                self.logger.info("\nNo more trials will be attempted.\n")
                break

            # Try to learn from this failure.
            self.logger.info("\nResponse is INCORRECT. Try to learn from this failure.\n")
            insight = await self.prompter.learn_from_failure(
                task, memory_section, response, expected_answer, work_history
            )
            self.logger.info("\nInsight:  {}\n".format(insight))
            new_insights.append(insight)
            last_insight = insight

        # Return the answer from the last loop.
        self.logger.info("\n{}\n".format(final_response))
        self.logger.leave_function()
        return final_response, successful_insight