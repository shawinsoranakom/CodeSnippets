def run(self, tmp: t.Optional[str] = None, task_vars: t.Optional[dict[str, t.Any]] = None) -> dict[str, t.Any]:

        result = super(ActionModule, self).run(tmp, task_vars)
        result['ansible_facts'] = {}

        # copy the value with list() so we don't mutate the config
        modules = list(C.config.get_config_value('FACTS_MODULES', variables=task_vars))
        self._handle_smart(modules, task_vars)

        parallel = task_vars.pop('ansible_facts_parallel', self._task.args.pop('parallel', None))

        failed: dict[str, t.Any] = {}
        skipped: dict[str, t.Any] = {}

        if parallel is None:
            if len(modules) > 1:
                parallel = True
            else:
                parallel = False
        else:
            parallel = boolean(parallel)

        timeout = self._task.args.get('gather_timeout', None)
        async_val = self._task.async_val

        if not parallel:
            # serially execute each module
            for fact_module in modules:
                # just one module, no need for fancy async
                mod_args = self._get_module_args(fact_module, task_vars)
                # TODO: use gather_timeout to cut module execution if module itself does not support gather_timeout
                res = self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=False)
                if res.get('failed', False):
                    failed[fact_module] = res
                elif res.get('skipped', False):
                    skipped[fact_module] = res
                else:
                    result = self._combine_task_result(result, res)

            self._remove_tmp_path(self._connection._shell.tmpdir)
        else:
            # do it async, aka parallel
            jobs: dict[str, t.Any] = {}

            for fact_module in modules:
                mod_args = self._get_module_args(fact_module, task_vars)

                #  if module does not handle timeout, use timeout to handle module, hijack async_val as this is what async_wrapper uses
                # TODO: make this action complain about async/async settings, use parallel option instead .. or remove parallel in favor of async settings?
                if timeout and 'gather_timeout' not in mod_args:
                    self._task.async_val = int(timeout)
                elif async_val != 0:
                    self._task.async_val = async_val
                else:
                    self._task.async_val = 0

                self._display.vvvv("Running %s" % fact_module)
                jobs[fact_module] = (self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=True))

            while jobs:
                for module in jobs:
                    poll_args = {'jid': jobs[module]['ansible_job_id'], '_async_dir': os.path.dirname(jobs[module]['results_file'])}
                    res = self._execute_module(module_name='ansible.legacy.async_status', module_args=poll_args, task_vars=task_vars, wrap_async=False)
                    if res.get('finished', False):
                        if res.get('failed', False):
                            failed[module] = res
                        elif res.get('skipped', False):
                            skipped[module] = res
                        else:
                            result = self._combine_task_result(result, res)
                        del jobs[module]
                        break
                    else:
                        time.sleep(0.1)
                else:
                    time.sleep(0.5)

        # restore value for post processing
        if self._task.async_val != async_val:
            self._task.async_val = async_val

        if skipped:
            result['msg'] = f"The following modules were skipped: {', '.join(skipped.keys())}."
            result['skipped_modules'] = skipped
            if len(skipped) == len(modules):
                result['skipped'] = True

        if failed:
            result['failed_modules'] = failed

            result.update(_error_utils.result_dict_from_captured_errors(
                msg=f"The following modules failed to execute: {', '.join(failed.keys())}.",
                errors=[r['exception'] for r in failed.values()],
            ))

        # tell executor facts were gathered
        result['ansible_facts']['_ansible_facts_gathered'] = True

        # hack to keep --verbose from showing all the setup module result
        result['_ansible_verbose_override'] = True

        return result