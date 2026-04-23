def reset(self, query_string: str = "", page_script_hash: str = "") -> None:
        self.cursors = {}
        self.widget_ids_this_run = set()
        self.widget_user_keys_this_run = set()
        self.form_ids_this_run = set()
        self.query_string = query_string
        self.page_script_hash = page_script_hash
        # Permit set_page_config when the ScriptRunContext is reused on a rerun
        self._set_page_config_allowed = True
        self._has_script_started = False
        self.command_tracking_deactivated: bool = False
        self.tracked_commands = []
        self.tracked_commands_counter = collections.Counter()