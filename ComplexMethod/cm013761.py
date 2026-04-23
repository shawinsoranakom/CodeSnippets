def _load_from_state_dict(
        self,
        state_dict,
        prefix,
        local_metadata,
        strict,
        missing_keys,
        unexpected_keys,
        error_msgs,
    ) -> None:
        version = local_metadata.get("version", None)
        # at version 1: removed running_mean and running_var when
        # track_running_stats=False (default)
        if version is None and not self.track_running_stats:
            running_stats_keys = []
            for name in ("running_mean", "running_var"):
                key = prefix + name
                if key in state_dict:
                    running_stats_keys.append(key)
            if len(running_stats_keys) > 0:
                error_msgs.append(
                    "Unexpected running stats buffer(s) {names} for {klass} "
                    "with track_running_stats=False. If state_dict is a "
                    "checkpoint saved before 0.4.0, this may be expected "
                    "because {klass} does not track running stats by default "
                    "since 0.4.0. Please remove these keys from state_dict. If "
                    "the running stats are actually needed, instead set "
                    "track_running_stats=True in {klass} to enable them. See "
                    "the documentation of {klass} for details.".format(
                        names=" and ".join(f'"{k}"' for k in running_stats_keys),
                        klass=self.__class__.__name__,
                    )
                )
                for key in running_stats_keys:
                    state_dict.pop(key)

        super()._load_from_state_dict(
            state_dict,
            prefix,
            local_metadata,
            strict,
            missing_keys,
            unexpected_keys,
            error_msgs,
        )