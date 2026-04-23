def _compute_environment_string(self, raw_environment_out=None) -> str:
        """
        Builds the environment string to be used when executing the remote task.
        """

        final_environment = dict()
        if self._task.environment is not None:
            environments = self._task.environment
            if not isinstance(environments, list):
                environments = [environments]

            # The order of environments matters to make sure we merge
            # in the parent's values first so those in the block then
            # task 'win' in precedence
            for environment in environments:
                if environment is None or len(environment) == 0:
                    continue
                temp_environment = self._templar.template(environment)
                if not isinstance(temp_environment, dict):
                    raise AnsibleError("environment must be a dictionary, received %s (%s)" % (temp_environment, type(temp_environment)))
                # very deliberately using update here instead of combine_vars, as
                # these environment settings should not need to merge sub-dicts
                final_environment.update(temp_environment)

        if len(final_environment) > 0:
            final_environment = self._templar.template(final_environment)

        if isinstance(raw_environment_out, dict):
            raw_environment_out.clear()
            raw_environment_out.update(final_environment)

        return self._connection._shell.env_prefix(**final_environment)