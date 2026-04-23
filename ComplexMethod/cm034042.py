def is_available(self, handle_exceptions=True):
        if super(RespawningLibMgr, self).is_available():
            return True

        for binary in self.CLI_BINARIES:
            try:
                bin_path = get_bin_path(binary)
            except ValueError:
                # Not an interesting exception to raise, just a speculative probe
                continue
            else:
                # It looks like this package manager is installed
                if not has_respawned():
                    # See if respawning will help
                    interpreter_path = probe_interpreters_for_module(self.INTERPRETERS, self.LIB)
                    if interpreter_path:
                        respawn_module(interpreter_path)
                        # The module will exit when the respawned copy completes

                if not handle_exceptions:
                    raise Exception(f'Found executable at {bin_path}. {missing_required_lib(self.LIB)}')

        if not handle_exceptions:
            raise Exception(missing_required_lib(self.LIB))

        return False