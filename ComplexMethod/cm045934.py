def init_res(self, stages_pattern, return_patterns=None, return_stages=None):

        if return_patterns and return_stages:
            return_stages = None

        if return_stages is True:
            return_patterns = stages_pattern
        # return_stages is int or bool
        if type(return_stages) is int:
            return_stages = [return_stages]
        if isinstance(return_stages, list):
            if max(return_stages) > len(stages_pattern) or min(return_stages) < 0:
                return_stages = [
                    val
                    for val in return_stages
                    if val >= 0 and val < len(stages_pattern)
                ]
            return_patterns = [stages_pattern[i] for i in return_stages]

        if return_patterns:
            self.update_res(return_patterns)