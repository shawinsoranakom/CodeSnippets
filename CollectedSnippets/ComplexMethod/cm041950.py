async def run_reflect(
        self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        screenshot_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{round_count}_after", local_save_dir=task_dir)
        )
        if not screenshot_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

        screenshot_after_labeled_path = task_dir.joinpath(f"{round_count}_after_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_after_labeled_path, elem_list=self.elem_list)
        img_base64 = encode_image(screenshot_after_labeled_path)
        if self.act_name == ActionOp.TAP.value:
            action = "tapping"
        elif self.act_name == ActionOp.LONG_PRESS.value:
            action = "long pressing"
        elif self.act_name == ActionOp.SWIPE.value:
            action = "swiping"
            if self.swipe_orient == SwipeOp.UP.value or self.swipe_orient == SwipeOp.DOWN.value:
                action = "v_swipe"
            elif self.swipe_orient == SwipeOp.LEFT.value or self.swipe_orient == SwipeOp.RIGHT.value:
                action = "h_swipe"
        else:
            # TODO Test for assignment, This error is eupiped with the next.
            logger.warning(f"Current action name parse failed, it's `{self.act_name}`")
            action = None
        context = reflect_template.format(
            action=action, ui_element=str(self.ui_area), task_desc=task_desc, last_act=last_act
        )
        node = await SELF_LEARN_REFLECT_NODE.fill(
            context=context, llm=self.llm, images=[self.screenshot_before_base64, img_base64]
        )

        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)

        prompt = node.compile(context=context, schema="json", mode="auto")
        ReflectLogItem(
            step=round_count,
            prompt=prompt,
            image_before=str(self.screenshot_before_path),
            image_after=str(screenshot_after_labeled_path),
            response=node.content,
        )

        op_param = reflect_parse_extarct(node.instruct_content.model_dump())
        if op_param.param_state == RunState.FINISH:
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        logger.info(
            f"reflect_parse_extarct decision: {op_param.decision}, "
            f"elem_list size: {len(self.elem_list)}, ui_area: {self.ui_area}"
        )
        # TODO here will cause `IndexError: list index out of range`.
        #  Maybe you should clink back to the desktop in the simulator
        resource_id = self.elem_list[int(self.ui_area) - 1].uid
        if op_param.decision == Decision.INEFFECTIVE.value:
            self.useless_list.append(resource_id)
            last_act = "NONE"  # TODO global
        elif op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value, Decision.SUCCESS.value]:
            if op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value]:
                self.useless_list.append(resource_id)
                last_act = "NONE"
                if op_param.decision == Decision.BACK.value:
                    action = EnvAction(action_type=EnvActionType.SYSTEM_BACK)
                    obs, _, _, _, info = env.step(action)
                    if info["res"] == ADB_EXEC_FAIL:
                        return AndroidActionOutput(action_state=RunState.FAIL)
            doc = op_param.documentation
            doc_path = docs_dir.joinpath(f"{resource_id}.txt")
            if doc_path.exists():
                try:
                    doc_content = ast.literal_eval(doc_path.read_text())
                except Exception as exp:
                    logger.error(f"ast parse doc: {doc_path} failed, exp: {exp}")
                    return AndroidActionOutput(action_state=RunState.FAIL)

                if doc_content[self.act_name]:
                    logger.info(f"Documentation for the element {resource_id} already exists.")
                    return AndroidActionOutput(action_state=RunState.FAIL)
            else:
                doc_content = DocContent()
                setattr(doc_content, self.act_name, doc)
            doc_path.write_text(str(doc_content))
        return AndroidActionOutput(data={"last_act": last_act})