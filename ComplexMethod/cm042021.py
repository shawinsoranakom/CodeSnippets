async def write_and_exec_code(self, instruction: str = ""):
        """Write a code block for current task and execute it in an interactive notebook environment.

        Args:
            instruction (optional, str): Further hints or notice other than the current task instruction, must be very concise and can be empty. Defaults to "".
        """
        if self.planner.plan:
            logger.info(f"Current task {self.planner.plan.current_task}")

        counter = 0
        success = False
        await self.execute_code.init_code()

        # plan info
        if self.planner.current_task:
            # clear task result from plan to save token, since it has been in memory
            plan_status = self.planner.get_plan_status(exclude=["task_result"])
            plan_status += f"\nFurther Task Instruction: {instruction}"
        else:
            return "No current_task found now. Please use command Plan.append_task to add a task first."

        # tool info
        if self.custom_tool_recommender:
            plan = self.planner.plan
            fixed = ["Terminal"] if "Terminal" in self.custom_tools else None
            tool_info = await self.custom_tool_recommender.get_recommended_tool_info(fixed=fixed, plan=plan)
        else:
            tool_info = ""

        # data info
        await self._check_data()

        while not success and counter < 3:
            ### write code ###
            logger.info("ready to WriteAnalysisCode")
            use_reflection = counter > 0 and self.use_reflection  # only use reflection after the first trial

            code = await self.write_code.run(
                user_requirement=self.planner.plan.goal,
                plan_status=plan_status,
                tool_info=tool_info,
                working_memory=self.rc.working_memory.get(),
                use_reflection=use_reflection,
                memory=self.rc.memory.get(self.memory_k),
            )
            self.rc.working_memory.add(Message(content=code, role="assistant", cause_by=WriteAnalysisCode))

            ### execute code ###
            result, success = await self.execute_code.run(code)
            print(result)

            self.rc.working_memory.add(Message(content=result, role="user", cause_by=ExecuteNbCode))

            ### process execution result ###
            counter += 1
            if success:
                task_result = TaskResult(code=code, result=result, is_success=success)
                self.planner.current_task.update_task_result(task_result)

        status = "Success" if success else "Failed"
        output = CODE_STATUS.format(code=code, status=status, result=result)
        if success:
            output += "The code written has been executed successfully."
        self.rc.working_memory.clear()
        return output