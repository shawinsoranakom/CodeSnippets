def load_extensions(self):
        "Fill self.extensions with data from the default and user configs."
        self.extensions = {}

        for ext_name in idleConf.GetExtensions(active_only=False):
            # Former built-in extensions are already filtered out.
            self.extensions[ext_name] = []

        for ext_name in self.extensions:
            default = set(self.ext_defaultCfg.GetOptionList(ext_name))
            user = set(self.ext_userCfg.GetOptionList(ext_name))
            opt_list = sorted(default | user)

            # Bring 'enable' options to the beginning of the list.
            enables = [opt_name for opt_name in opt_list
                       if opt_name.startswith('enable')]
            for opt_name in enables:
                opt_list.remove(opt_name)
            opt_list = enables + opt_list

            for opt_name in opt_list:
                if opt_name in default:
                    def_str = self.ext_defaultCfg.Get(
                            ext_name, opt_name, raw=True)
                else:
                    def_str = self.ext_userCfg.Get(
                            ext_name, opt_name, raw=True)
                try:
                    def_obj = {'True':True, 'False':False}[def_str]
                    opt_type = 'bool'
                except KeyError:
                    try:
                        def_obj = int(def_str)
                        opt_type = 'int'
                    except ValueError:
                        def_obj = def_str
                        opt_type = None
                try:
                    value = self.ext_userCfg.Get(
                            ext_name, opt_name, type=opt_type, raw=True,
                            default=def_obj)
                except ValueError:  # Need this until .Get fixed.
                    value = def_obj  # Bad values overwritten by entry.
                var = StringVar(self)
                var.set(str(value))

                self.extensions[ext_name].append({'name': opt_name,
                                                  'type': opt_type,
                                                  'default': def_str,
                                                  'value': value,
                                                  'var': var,
                                                 })