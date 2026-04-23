def console(self, local_vars):
        if not os.isatty(sys.stdin.fileno()):
            local_vars['__name__'] = '__main__'
            exec(sys.stdin.read(), local_vars)
        else:
            if 'env' not in local_vars:
                print('No environment set, use `%s shell -d dbname` to get one.' % sys.argv[0])
            for i in sorted(local_vars):
                print('%s: %s' % (i, local_vars[i]))

            pythonstartup = config.options.get('shell_file') or os.environ.get('PYTHONSTARTUP')

            preferred_interface = config.options.get('shell_interface')
            if preferred_interface:
                shells_to_try = [preferred_interface, 'python']
            else:
                shells_to_try = self.supported_shells

            for shell in shells_to_try:
                try:
                    shell_func = getattr(self, shell)
                    return shell_func(local_vars, pythonstartup)
                except ImportError:
                    pass
                except Exception:
                    _logger.warning("Could not start '%s' shell.", shell)
                    _logger.debug("Shell error:", exc_info=True)