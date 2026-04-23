def _parse_from_string(self, options_str):
        for kv in options_str.replace(" ", "").split(";"):
            key, value = kv.split("=")
            if key == "batch_range":
                value_list = value.replace("[", "").replace("]", "").split(",")
                value_list = list(map(int, value_list))
                if (
                    len(value_list) >= 2
                    and value_list[0] >= 0
                    and value_list[1] > value_list[0]
                ):
                    self._options[key] = value_list
            elif key == "exit_on_finished":
                self._options[key] = value.lower() in ("yes", "true", "t", "1")
            elif key in ["state", "sorted_key", "tracer_option", "profile_path"]:
                self._options[key] = value
            elif key == "timer_only":
                self._options[key] = value