async def run_self_learn(
        self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        extra_config = config.extra
        screenshot_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{round_count}_before", local_save_dir=task_dir)
        )
        xml_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_XML, xml_name=f"{round_count}", local_save_dir=task_dir)
        )
        if not screenshot_path.exists() or not xml_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

        elem_list = elem_list_from_xml_tree(xml_path, self.useless_list, extra_config.get("min_dist", 30))

        screenshot_before_labeled_path = task_dir.joinpath(f"{round_count}_before_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_before_labeled_path, elem_list)
        img_base64 = encode_image(screenshot_before_labeled_path)
        self.screenshot_before_base64 = img_base64
        self.screenshot_before_path = screenshot_before_labeled_path

        self_explore_template = screenshot_parse_self_explore_template
        context = self_explore_template.format(task_description=task_desc, last_act=last_act)

        node = await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm, images=[img_base64])
        logger.debug(f"fill result:{node}")
        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)
        prompt = node.compile(context=context, schema="json", mode="auto")
        # Modify WindowsPath to Str
        OpLogItem(step=round_count, prompt=prompt, image=str(screenshot_before_labeled_path), response=node.content)
        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on=False)
        # TODO Modify Op_param. When op_param.action is FINISH, how to solve this ?
        if op_param.param_state == RunState.FINISH:
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        if isinstance(op_param, TapOpParam):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.SYSTEM_TAP, coord=(x, y))
        elif isinstance(op_param, TextOpParam):
            action = EnvAction(action_type=EnvActionType.USER_INPUT, input_txt=op_param.input_str)
        elif isinstance(op_param, LongPressOpParam):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.USER_LONGPRESS, coord=(x, y))
        elif isinstance(op_param, SwipeOpParam):
            self.ui_area = op_param.area
            self.swipe_orient = op_param.swipe_orient
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(
                action_type=EnvActionType.USER_SWIPE, coord=(x, y), orient=op_param.swipe_orient, dist=op_param.dist
            )

        obs, _, _, _, info = env.step(action)
        action_res = info["res"]
        if action_res == ADB_EXEC_FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        self.elem_list = elem_list
        self.act_name = op_param.act_name
        return AndroidActionOutput()