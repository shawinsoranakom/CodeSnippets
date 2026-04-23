def iter_all_configs(self):
        for use_main_obmalloc in (True, False):
            for allow_fork in (True, False):
                for allow_exec in (True, False):
                    for allow_threads in (True, False):
                        for allow_daemon in (True, False):
                            for checkext in (True, False):
                                for gil in ('shared', 'own', 'default'):
                                    yield types.SimpleNamespace(
                                        use_main_obmalloc=use_main_obmalloc,
                                        allow_fork=allow_fork,
                                        allow_exec=allow_exec,
                                        allow_threads=allow_threads,
                                        allow_daemon_threads=allow_daemon,
                                        check_multi_interp_extensions=checkext,
                                        gil=gil,
                                    )