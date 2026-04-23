async def run(
        self, context: list[Message] = [], plan: Plan = None, trigger: str = ReviewConst.TASK_REVIEW_TRIGGER
    ) -> Tuple[str, bool]:
        if plan:
            logger.info("Current overall plan:")
            logger.info(
                "\n".join(
                    [f"{task.task_id}: {task.instruction}, is_finished: {task.is_finished}" for task in plan.tasks]
                )
            )

        logger.info("Most recent context:")
        latest_action = context[-1].cause_by if context and context[-1].cause_by else ""
        review_instruction = (
            ReviewConst.TASK_REVIEW_INSTRUCTION
            if trigger == ReviewConst.TASK_REVIEW_TRIGGER
            else ReviewConst.CODE_REVIEW_INSTRUCTION
        )
        prompt = (
            f"This is a <{trigger}> review. Please review output from {latest_action}\n"
            f"{review_instruction}\n"
            f"{ReviewConst.EXIT_INSTRUCTION}\n"
            "Please type your review below:\n"
        )

        rsp = await get_human_input(prompt)

        if rsp.lower() in ReviewConst.EXIT_WORDS:
            exit()

        # Confirmation can be one of "confirm", "continue", "c", "yes", "y" exactly, or sentences containing "confirm".
        # One could say "confirm this task, but change the next task to ..."
        confirmed = rsp.lower() in ReviewConst.CONTINUE_WORDS or ReviewConst.CONTINUE_WORDS[0] in rsp.lower()

        return rsp, confirmed