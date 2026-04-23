def _set_become_plugin(self, cvars, templar, connection):
        # load become plugin if needed
        if cvars.get('ansible_become') is not None:
            become = boolean(templar.template(cvars['ansible_become']))
        else:
            become = self._task.become

        if become:
            if cvars.get('ansible_become_method'):
                become_plugin = self._get_become(templar.template(cvars['ansible_become_method']))
            else:
                become_plugin = self._get_become(self._task.become_method)

        else:
            # If become is not enabled on the task it needs to be removed from the connection plugin
            # https://github.com/ansible/ansible/issues/78425
            become_plugin = None

        try:
            connection.set_become_plugin(become_plugin)
        except AttributeError:
            # Older connection plugin that does not support set_become_plugin
            pass

        if become_plugin:
            if getattr(connection.become, 'require_tty', False) and not getattr(connection, 'has_tty', False):
                raise AnsibleError(
                    "The '%s' connection does not provide a TTY which is required for the selected "
                    "become plugin: %s." % (connection._load_name, become_plugin.name)
                )

            # Backwards compat for connection plugins that don't support become plugins
            # Just do this unconditionally for now, we could move it inside of the
            # AttributeError above later
            self._play_context.set_become_plugin(become_plugin.name)