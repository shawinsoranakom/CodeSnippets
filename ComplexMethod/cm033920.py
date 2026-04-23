def _make_tmp_path(self, remote_user: str | None = None) -> str:
        """
        Create and return a temporary path on a remote box.
        """

        # Network connection plugins (network_cli, netconf, etc.) execute on the controller, rather than the remote host.
        # As such, we want to avoid using remote_user for paths  as remote_user may not line up with the local user
        # This is a hack and should be solved by more intelligent handling of remote_tmp in 2.7
        if getattr(self._connection, '_remote_is_local', False):
            tmpdir = C.DEFAULT_LOCAL_TMP
        else:
            # NOTE: shell plugins should populate this setting anyways, but they dont do remote expansion, which
            # we need for 'non posix' systems like cloud-init and solaris
            tmpdir = self._remote_expand_user(self.get_shell_option('remote_tmp', default='~/.ansible/tmp'), sudoable=False)

        become_unprivileged = self._is_become_unprivileged()
        basefile = self._connection._shell._generate_temp_dir_name()

        cmd = None
        in_data = None
        if self._connection.is_pipelining_enabled(wrap_async=False):
            cmd_details = self._connection._shell._mkdtemp2(basefile=basefile, system=become_unprivileged, tmpdir=tmpdir)
            cmd = cmd_details.command
            in_data = cmd_details.input_data
        else:
            cmd = self._connection._shell.mkdtemp(basefile=basefile, system=become_unprivileged, tmpdir=tmpdir)
        result = self._low_level_execute_command(cmd, in_data=in_data, sudoable=False)

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self._connection.transport in ('ssh',):

                if display.verbosity > 3:
                    output = u'SSH encountered an unknown error. The output was:\n%s%s' % (result['stdout'], result['stderr'])
                else:
                    output = (u'SSH encountered an unknown error during the connection. '
                              'We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue')

            elif u'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = ('Failed to create temporary directory. '
                          'In some cases, you may have been able to authenticate and did not have permissions on the target directory. '
                          'Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp", for more error information use -vvv. '
                          'Failed command was: %s, exited with result %d' % (cmd, result['rc']))
            if 'stdout' in result and result['stdout'] != u'':
                output = output + u", stdout output: %s" % result['stdout']
            if display.verbosity > 3 and 'stderr' in result and result['stderr'] != u'':
                output += u", stderr output: %s" % result['stderr']
            raise AnsibleConnectionFailure(output)
        else:
            self._cleanup_remote_tmp = True

        try:
            stdout_parts = result['stdout'].strip().split('%s=' % basefile, 1)
            rc = self._connection._shell.join_path(stdout_parts[-1], u'').splitlines()[-1]
        except IndexError:
            # stdout was empty or just space, set to / to trigger error in next if
            rc = '/'

        # Catch failure conditions, files should never be
        # written to locations in /.
        if rc == '/':
            raise AnsibleError('failed to resolve remote temporary directory from %s: `%s` returned empty string' % (basefile, cmd))

        self._connection._shell.tmpdir = rc

        return rc