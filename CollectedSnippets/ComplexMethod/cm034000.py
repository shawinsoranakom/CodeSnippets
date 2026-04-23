def _file_transport_command(self, in_path: str, out_path: str, sftp_action: str) -> tuple[int, bytes, bytes]:
        # scp and sftp require square brackets for IPv6 addresses, but
        # accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host

        smart_methods = ['sftp', 'scp', 'piped']

        # Windows does not support dd so we cannot use the piped method
        if getattr(self._shell, "_IS_WINDOWS", False):
            smart_methods.remove('piped')

        # Transfer methods to try
        methods = []

        # Use the transfer_method option if set
        ssh_transfer_method = self.get_option('ssh_transfer_method')

        if ssh_transfer_method == 'smart':
            methods = smart_methods
        else:
            methods = [ssh_transfer_method]

        # NOTE: if passing a list to build_command, no need to quote those paths,
        # for strings use shlex.quote for local/controller and self._shell.quote for target
        for method in methods:
            returncode = stdout = stderr = None
            match method:
                case 'sftp':
                    cmd = self._build_command(self.get_option('sftp_executable'), method, to_bytes(host))
                    in_data = f"{sftp_action} {shlex.quote(in_path)} {shlex.quote(out_path)}\n"
                    in_data = to_bytes(in_data, nonstring='passthru')
                    (returncode, stdout, stderr) = self._bare_run(cmd, in_data, checkrc=False)
                case 'scp':
                    scp = self.get_option('scp_executable')
                    if sftp_action == 'get':
                        cmd = self._build_command(scp, method, f'{host}:{self._shell.quote(in_path)}', out_path)
                    else:
                        cmd = self._build_command(scp, method, in_path, f'{host}:{self._shell.quote(out_path)}')
                    in_data = None
                    (returncode, stdout, stderr) = self._bare_run(cmd, in_data, checkrc=False)
                case 'piped':
                    if sftp_action == 'get':
                        # we pass sudoable=False to disable pty allocation, which
                        # would end up mixing stdout/stderr and screwing with newlines
                        (returncode, stdout, stderr) = self.exec_command(f'dd if={self._shell.quote(in_path)} bs={BUFSIZE}', sudoable=False)
                        with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb+') as out_file:
                            out_file.write(stdout)
                    else:
                        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as f:
                            in_data = to_bytes(f.read(), nonstring='passthru')
                        if not in_data:
                            count = ' count=0'
                        else:
                            count = ''
                        (returncode, stdout, stderr) = self.exec_command(f'dd of={self._shell.quote(out_path)} bs={BUFSIZE}{count}',
                                                                         in_data=in_data, sudoable=False)

            # Check the return code and rollover to next method if failed
            if returncode == 0:
                return (returncode, stdout, stderr)
            else:
                # If not in smart mode, the data will be printed by the raise below
                if len(methods) > 1:
                    display.warning(u'%s transfer mechanism failed on %s. Use ANSIBLE_DEBUG=1 to see detailed information' % (method, host))
                    display.debug(u'%s' % to_text(stdout))
                    display.debug(u'%s' % to_text(stderr))

        if returncode == 255:
            raise AnsibleConnectionFailure("Failed to connect to the host via %s: %s" % (method, to_native(stderr)))
        else:
            raise AnsibleError("failed to transfer file to %s %s:\n%s\n%s" %
                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))