async def _act(self) -> Message:
        if self.input_args.project_path:
            await init_python_folder(self.repo.tests.workdir)
        if self.test_round > self.test_round_allowed:
            kvs = self.input_args.model_dump()
            kvs["changed_test_filenames"] = [
                str(self.repo.tests.workdir / i) for i in list(self.repo.tests.changed_files.keys())
            ]
            result_msg = AIMessage(
                content=f"Exceeding {self.test_round_allowed} rounds of tests, stop. "
                + "\n".join(list(self.repo.tests.changed_files.keys())),
                cause_by=WriteTest,
                instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteTestOutput"),
                send_to=MESSAGE_ROUTE_TO_NONE,
            )
            return result_msg

        code_filters = any_to_str_set({PrepareDocuments, SummarizeCode})
        test_filters = any_to_str_set({WriteTest, DebugError})
        run_filters = any_to_str_set({RunCode})
        for msg in self.rc.news:
            # Decide what to do based on observed msg type, currently defined by human,
            # might potentially be moved to _think, that is, let the agent decides for itself
            if msg.cause_by in code_filters:
                # engineer wrote a code, time to write a test for it
                await self._write_test(msg)
            elif msg.cause_by in test_filters:
                # I wrote or debugged my test code, time to run it
                await self._run_code(msg)
            elif msg.cause_by in run_filters:
                # I ran my test code, time to fix bugs, if any
                await self._debug_error(msg)
            elif msg.cause_by == any_to_str(UserRequirement):
                return await self._parse_user_requirement(msg)
        self.test_round += 1
        kvs = self.input_args.model_dump()
        kvs["changed_test_filenames"] = [
            str(self.repo.tests.workdir / i) for i in list(self.repo.tests.changed_files.keys())
        ]
        return AIMessage(
            content=f"Round {self.test_round} of tests done",
            instruct_content=AIMessage.create_instruct_value(kvs=kvs, class_name="WriteTestOutput"),
            cause_by=WriteTest,
            send_to=MESSAGE_ROUTE_TO_NONE,
        )