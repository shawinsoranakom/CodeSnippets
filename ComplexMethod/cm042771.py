def log_params(self):
        if self.disabled:
            return
        from encoder import params_data
        from encoder import params_model
        param_string = "<b>Model parameters</b>:<br>"
        for param_name in (p for p in dir(params_model) if not p.startswith("__")):
            value = getattr(params_model, param_name)
            param_string += "\t%s: %s<br>" % (param_name, value)
        param_string += "<b>Data parameters</b>:<br>"
        for param_name in (p for p in dir(params_data) if not p.startswith("__")):
            value = getattr(params_data, param_name)
            param_string += "\t%s: %s<br>" % (param_name, value)
        self.vis.text(param_string, opts={"title": "Parameters"})