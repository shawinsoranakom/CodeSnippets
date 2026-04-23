def _execute_remote_stat(self, path, all_vars, follow, tmp=None, checksum=True):
        """
        Get information from remote file.
        """
        if tmp is not None:
            display.warning('_execute_remote_stat no longer honors the tmp parameter. Action'
                            ' plugins should set self._connection._shell.tmpdir to share'
                            ' the tmpdir')
        del tmp  # No longer used

        module_args = dict(
            path=path,
            follow=follow,
            get_checksum=checksum,
            get_size=False,  # ansible.windows.win_stat added this in 1.11.0
            checksum_algorithm='sha1',
        )
        # Unknown opts are ignored as module_args could be specific for the
        # module that is being executed.
        mystat = self._execute_module(module_name='ansible.legacy.stat', module_args=module_args, task_vars=all_vars,
                                      wrap_async=False, ignore_unknown_opts=True)

        if mystat.get('failed'):
            msg = mystat.get('module_stderr')
            if not msg:
                msg = mystat.get('module_stdout')
            if not msg:
                msg = mystat.get('msg')
            raise AnsibleError('Failed to get information on remote file (%s): %s' % (path, msg))

        if not mystat['stat']['exists']:
            # empty might be matched, 1 should never match, also backwards compatible
            mystat['stat']['checksum'] = '1'

        # happens sometimes when it is a dir and not on bsd
        if 'checksum' not in mystat['stat']:
            mystat['stat']['checksum'] = ''
        elif not isinstance(mystat['stat']['checksum'], str):
            raise AnsibleError("Invalid checksum returned by stat: expected a string type but got %s" % type(mystat['stat']['checksum']))

        return mystat['stat']