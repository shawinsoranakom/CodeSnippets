def update_til_start_task(self, role: Experimenter, backward: bool = True):
        if backward:
            # make sure the previous task instructions are matched
            assert (
                self.start_task_id == role.start_task_id - 1
            ), f"start_task_id: {self.start_task_id}, role.start_task_id: {role.start_task_id}"
            for i in range(self.start_task_id):
                if (
                    self.planner.plan.task_map[str(self.start_task_id)].instruction
                    != role.planner.plan.task_map[str(self.start_task_id)].instruction
                ):
                    mcts_logger.info("Previous task instructions not matched")
                    self.remap_tasks()
                    return
            # copy new role's task (self.start_task_id) to current role
            self.planner.plan.task_map[str(self.start_task_id)] = role.planner.plan.task_map[
                str(self.start_task_id)
            ].model_copy()
            self.remap_tasks()

        else:
            assert (
                self.start_task_id == role.start_task_id + 1
            ), f"start_task_id: {self.start_task_id}, role.start_task_id: {role.start_task_id}"
            if int(role.planner.plan.current_task_id) > self.start_task_id:
                for i in range(role.start_task_id):
                    self.planner.plan.task_map[str(i)] = role.planner.plan.task_map[str(i)].model_copy()
            self.remap_tasks()