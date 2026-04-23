def run(self, tmp=None, task_vars=None):
        """ Load yml files recursively from a directory.
        """
        del tmp  # tmp no longer has any effect

        if task_vars is None:
            task_vars = dict()

        self.show_content = True
        self.included_files = []

        # Validate arguments
        dirs = 0
        files = 0
        for arg in self._task.args:
            if arg in self.VALID_DIR_ARGUMENTS:
                dirs += 1
            elif arg in self.VALID_FILE_ARGUMENTS:
                files += 1
            elif arg in self.VALID_ALL:
                pass
            else:
                raise AnsibleError(f'{arg} is not a valid option in include_vars', obj=arg)

        if dirs and files:
            raise AnsibleError("You are mixing file only and dir only arguments, these are incompatible", obj=self._task.args)

        # set internal vars from args
        self._set_args()

        results = dict()
        failed = False
        if self.source_dir:
            self._set_dir_defaults()
            self._set_root_dir()
            if not path.exists(self.source_dir):
                failed = True
                err_msg = f"{self.source_dir} directory does not exist"
            elif not path.isdir(self.source_dir):
                failed = True
                err_msg = f"{self.source_dir} is not a directory"
            else:
                for root_dir, filenames in self._traverse_dir_depth():
                    failed, err_msg, updated_results = self._load_files_in_dir(root_dir, filenames)
                    if failed:
                        break
                    results.update(updated_results)
        else:
            try:
                self.source_file = self._find_needle('vars', self.source_file)
                failed, err_msg, updated_results = (
                    self._load_files(self.source_file)
                )
                if not failed:
                    results.update(updated_results)

            except AnsibleError as e:
                failed = True
                err_msg = to_native(e)

        if self.return_results_as_name:
            scope = dict()
            scope[self.return_results_as_name] = results
            results = scope

        result = super(ActionModule, self).run(task_vars=task_vars)

        if failed:
            result['failed'] = failed
            result['message'] = err_msg
        elif self.hash_behaviour is not None and self.hash_behaviour != C.DEFAULT_HASH_BEHAVIOUR:
            merge_hashes = self.hash_behaviour == 'merge'
            existing_variables = {k: v for k, v in task_vars.items() if k in results}
            results = combine_vars(existing_variables, results, merge=merge_hashes)

        result['ansible_included_var_files'] = self.included_files
        self.register_host_variables(results, VariableLayer.INCLUDE_VARS)
        # until INJECT_FACTS_AS_VARS is removed, this prevent ansible_facts in the action result from getting added to the vars cache
        self.register_host_variables({}, VariableLayer.CACHEABLE_FACT)
        result['ansible_facts'] = results
        result['_ansible_no_log'] = not self.show_content

        return result