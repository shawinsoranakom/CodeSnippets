def set_script_name(self, val):
        clear_script_prefix()
        if val is not None:
            set_script_prefix(val)