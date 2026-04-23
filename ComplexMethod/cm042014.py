async def _think(self) -> bool:
        if not self.rc.news:
            return False
        msg = self.rc.news[0]
        input_args = msg.instruct_content
        if msg.cause_by in {any_to_str(WriteTasks), any_to_str(FixBug)}:
            self.input_args = input_args
            self.repo = ProjectRepo(input_args.project_path)
            if self.repo.src_relative_path is None:
                path = get_project_srcs_path(self.repo.workdir)
                self.repo.with_src_path(path)
        write_plan_and_change_filters = any_to_str_set([PrepareDocuments, WriteTasks, FixBug])
        write_code_filters = any_to_str_set([WriteTasks, WriteCodePlanAndChange, SummarizeCode])
        summarize_code_filters = any_to_str_set([WriteCode, WriteCodeReview])
        if self.config.inc and msg.cause_by in write_plan_and_change_filters:
            logger.debug(f"TODO WriteCodePlanAndChange:{msg.model_dump_json()}")
            await self._new_code_plan_and_change_action(cause_by=msg.cause_by)
            return bool(self.rc.todo)
        if msg.cause_by in write_code_filters:
            logger.debug(f"TODO WriteCode:{msg.model_dump_json()}")
            await self._new_code_actions()
            return bool(self.rc.todo)
        if msg.cause_by in summarize_code_filters and msg.sent_from == any_to_str(self):
            logger.debug(f"TODO SummarizeCode:{msg.model_dump_json()}")
            await self._new_summarize_actions()
            return bool(self.rc.todo)
        return False