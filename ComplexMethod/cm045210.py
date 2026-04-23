async def retrieve_relevant_memos(self, task: str) -> List[Memo]:
        """
        Retrieves any memos from memory that seem relevant to the task.
        """
        self.logger.enter_function()

        if self.memory_bank.contains_memos():
            self.logger.info("\nCURRENT TASK:")
            self.logger.info(task)

            # Get a list of topics from the generalized task.
            if self.generalize_task:
                generalized_task = await self.prompter.generalize_task(task, revise=self.revise_generalized_task)
            else:
                generalized_task = task
            if self.generate_topics:
                task_topics = await self.prompter.find_index_topics(generalized_task)
            else:
                task_topics = [generalized_task]
            self.logger.info("\nTOPICS EXTRACTED FROM TASK:")
            self.logger.info("\n".join(task_topics))
            self.logger.info("")

            # Retrieve relevant memos from the memory bank.
            memo_list = self.memory_bank.get_relevant_memos(topics=task_topics)

            # Apply a final validation stage to keep only the memos that the LLM concludes are sufficiently relevant.
            validated_memos: List[Memo] = []
            for memo in memo_list:
                if len(validated_memos) >= self.max_memos_to_retrieve:
                    break
                if (not self.validate_memos) or await self.prompter.validate_insight(memo.insight, task):
                    validated_memos.append(memo)

            self.logger.info("\n{} VALIDATED MEMOS".format(len(validated_memos)))
            for memo in validated_memos:
                if memo.task is not None:
                    self.logger.info("\n  TASK: {}".format(memo.task))
                self.logger.info("\n  INSIGHT: {}".format(memo.insight))
        else:
            self.logger.info("\nNO SUFFICIENTLY RELEVANT MEMOS WERE FOUND IN MEMORY")
            validated_memos = []

        self.logger.leave_function()
        return validated_memos