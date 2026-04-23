def _set_internal_properties(self, argument_spec=None, module_parameters=None):
        if argument_spec is None:
            argument_spec = self.argument_spec
        if module_parameters is None:
            module_parameters = self.params

        for k in PASS_VARS:
            # handle setting internal properties from internal ansible vars
            param_key = '_ansible_%s' % k
            if param_key in module_parameters:
                if k in PASS_BOOLS:
                    setattr(self, PASS_VARS[k][0], self.boolean(module_parameters[param_key]))
                else:
                    setattr(self, PASS_VARS[k][0], module_parameters[param_key])

                # clean up internal top level params:
                if param_key in self.params:
                    del self.params[param_key]
            else:
                # use defaults if not already set
                if not hasattr(self, PASS_VARS[k][0]):
                    setattr(self, PASS_VARS[k][0], PASS_VARS[k][1])