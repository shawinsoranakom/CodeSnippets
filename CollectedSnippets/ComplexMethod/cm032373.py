def gen_conf(self):
        conf = {}
        def get_attr(nm):
            try:
                return getattr(self, nm)
            except Exception:
                pass

        if int(self.max_tokens) > 0 and get_attr("maxTokensEnabled"):
            conf["max_tokens"] = int(self.max_tokens)
        if float(self.temperature) > 0 and get_attr("temperatureEnabled"):
            conf["temperature"] = float(self.temperature)
        if float(self.top_p) > 0 and get_attr("topPEnabled"):
            conf["top_p"] = float(self.top_p)
        if float(self.presence_penalty) > 0 and get_attr("presencePenaltyEnabled"):
            conf["presence_penalty"] = float(self.presence_penalty)
        if float(self.frequency_penalty) > 0 and get_attr("frequencyPenaltyEnabled"):
            conf["frequency_penalty"] = float(self.frequency_penalty)
        return conf