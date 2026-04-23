def _log_invocation(self):
        """ log that ansible ran the module """
        # TODO: generalize a separate log function and make log_invocation use it
        # Sanitize possible password argument when logging.
        log_args = dict()

        for param in self.params:
            canon = self.aliases.get(param, param)
            arg_opts = self.argument_spec.get(canon, {})
            no_log = arg_opts.get('no_log', None)

            # try to proactively capture password/passphrase fields
            if no_log is None and PASSWORD_MATCH.search(param):
                log_args[param] = 'NOT_LOGGING_PASSWORD'
                self.warn('Module did not set no_log for %s' % param)
            elif self.boolean(no_log):
                log_args[param] = 'NOT_LOGGING_PARAMETER'
            else:
                param_val = self.params[param]
                if not isinstance(param_val, (str, bytes)):
                    param_val = str(param_val)
                elif isinstance(param_val, str):
                    param_val = param_val.encode('utf-8')
                log_args[param] = heuristic_log_sanitize(param_val, self.no_log_values)

        msg = ['%s=%s' % (to_native(arg), to_native(val)) for arg, val in log_args.items()]
        if msg:
            msg = 'Invoked with %s' % ' '.join(msg)
        else:
            msg = 'Invoked'

        self.log(msg, log_args=log_args)