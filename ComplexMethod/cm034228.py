def default(self, line, forceshell=False):
        """ actually runs modules """
        if line.startswith("#"):
            return False

        if not self.cwd:
            display.error("No host found")
            return False

        # defaults
        module = 'shell'
        module_args = line

        if forceshell is not True:
            possible_module, *possible_args = line.split()
            if module_loader.find_plugin(possible_module):
                # we found module!
                module = possible_module
                if possible_args:
                    module_args = ' '.join(possible_args)
                else:
                    module_args = ''

        module_args = TrustedAsTemplate().tag(module_args)

        if self.callback:
            cb = self.callback
        elif C.DEFAULT_LOAD_CALLBACK_PLUGINS and C.DEFAULT_STDOUT_CALLBACK != 'default':
            cb = C.DEFAULT_STDOUT_CALLBACK
        else:
            cb = 'minimal'

        result = None
        try:
            check_raw = module in C._ACTION_ALLOWS_RAW_ARGS
            task = dict(action=module, args=parse_kv(module_args, check_raw=check_raw), timeout=self.task_timeout)
            play_ds = dict(
                name="Ansible Shell",
                hosts=self.cwd,
                gather_facts='no',
                tasks=[task],
                remote_user=self.remote_user,
                become=self.become,
                become_user=self.become_user,
                become_method=self.become_method,
                check_mode=self.check_mode,
                diff=self.diff,
                collections=self.collections,
            )
            play = Play().load(play_ds, variable_manager=self.variable_manager, loader=self.loader)
        except Exception as e:
            display.error(u"Unable to build command: %s" % to_text(e))
            return False

        try:
            # now create a task queue manager to execute the play
            self._tqm = None
            try:
                self._tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    passwords=self.passwords,
                    stdout_callback_name=cb,
                    run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                    run_tree=False,
                    forks=self.forks,
                )

                result = self._tqm.run(play)
                display.debug(result)
            except AnsibleEndPlay as e:
                result = e.result
            finally:
                if self._tqm:
                    self._tqm.cleanup()
                if self.loader:
                    self.loader.cleanup_all_tmp_files()

            if result is None:
                display.error("No hosts found")
                return False
        except KeyboardInterrupt:
            display.error('User interrupted execution')
            return False
        except Exception as ex:
            display.error(ex)
            return False