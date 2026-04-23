def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        stats = {'data': {}, 'per_host': False, 'aggregate': True}

        if self._task.args:
            data = self._task.args.get('data', {})

            if not isinstance(data, dict):
                data = self._templar.template(data)

            if not isinstance(data, dict):
                result['failed'] = True
                result['msg'] = "The 'data' option needs to be a dictionary/hash"
                return result

            # set boolean options, defaults are set above in stats init
            for opt in ['per_host', 'aggregate']:
                val = self._task.args.get(opt, None)
                if val is not None:
                    if not isinstance(val, bool):
                        stats[opt] = boolean(self._templar.template(val), strict=False)
                    else:
                        stats[opt] = val

            for (k, v) in data.items():
                k = self._templar.template(k)

                validate_variable_name(k)

                stats['data'][k] = self._templar.template(v)

        result['changed'] = False
        result['ansible_stats'] = stats

        return result