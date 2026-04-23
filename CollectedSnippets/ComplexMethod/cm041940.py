def __init__(self, **data):
        super().__init__(**data)
        self._watch([UserRequirement, AndroidActionOutput])
        extra_config = config.extra
        self.task_desc = extra_config.get("task_desc", "Just explore any app in this phone!")
        app_name = extra_config.get("app_name", "demo")
        data_dir = self.output_root_dir.absolute().joinpath("output") or EXAMPLE_PATH.joinpath(
            "android_assistant/output"
        )
        cur_datetime = datetime.fromtimestamp(int(time.time())).strftime("%Y-%m-%d_%H-%M-%S")

        """Firstly, we decide the state with user config, further, we can do it automatically, like if it's new app,
        run the learn first and then do the act stage or learn it during the action.
        """
        stage = extra_config.get("stage")
        mode = extra_config.get("mode")
        if stage == "learn" and mode == "manual":
            # choose ManualRecord and then run ParseRecord
            # Remember, only run each action only one time, no need to run n_round.
            self.set_actions([ManualRecord, ParseRecord])
            self.task_dir = data_dir.joinpath(app_name, f"manual_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, "manual_docs")
        elif stage == "learn" and mode == "auto":
            # choose SelfLearnAndReflect to run
            self.set_actions([SelfLearnAndReflect])
            self.task_dir = data_dir.joinpath(app_name, f"auto_learn_{cur_datetime}")
            self.docs_dir = data_dir.joinpath(app_name, "auto_docs")
        elif stage == "act":
            # choose ScreenshotParse to run
            self.set_actions([ScreenshotParse])
            self.task_dir = data_dir.joinpath(app_name, f"act_{cur_datetime}")
            if mode == "manual":
                self.docs_dir = data_dir.joinpath(app_name, "manual_docs")
            else:
                self.docs_dir = data_dir.joinpath(app_name, "auto_docs")
        else:
            raise ValueError(f"invalid stage: {stage}, mode: {mode}")

        self._check_dir()

        self._set_react_mode(RoleReactMode.BY_ORDER)