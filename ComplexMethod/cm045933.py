def init_net(
        self,
        stages_pattern=None,
        return_patterns=None,
        return_stages=None,
        freeze_befor=None,
        stop_after=None,
        *args,
        **kwargs,
    ):
        # init the output of net
        if return_patterns or return_stages:
            if return_patterns and return_stages:
                msg = f"The 'return_patterns' would be ignored when 'return_stages' is set."

                return_stages = None

            if return_stages is True:
                return_patterns = stages_pattern

            # return_stages is int or bool
            if type(return_stages) is int:
                return_stages = [return_stages]
            if isinstance(return_stages, list):
                if max(return_stages) > len(stages_pattern) or min(return_stages) < 0:
                    msg = f"The 'return_stages' set error. Illegal value(s) have been ignored. The stages' pattern list is {stages_pattern}."

                    return_stages = [
                        val
                        for val in return_stages
                        if val >= 0 and val < len(stages_pattern)
                    ]
                return_patterns = [stages_pattern[i] for i in return_stages]

            if return_patterns:
                # call update_res function after the __init__ of the object has completed execution, that is, the constructing of layer or model has been completed.
                def update_res_hook(layer, input):
                    self.update_res(return_patterns)

                self.register_forward_pre_hook(update_res_hook)

        # freeze subnet
        if freeze_befor is not None:
            self.freeze_befor(freeze_befor)

        # set subnet to Identity
        if stop_after is not None:
            self.stop_after(stop_after)