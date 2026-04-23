def fetch_file(self, in_path: str, out_path: str) -> None:
        super(Connection, self).fetch_file(in_path, out_path)
        out_path = out_path.replace('\\', '/')
        # consistent with other connection plugins, we assume the caller has created the target dir
        display.vvv('FETCH "%s" TO "%s"' % (in_path, out_path), host=self._winrm_host)
        buffer_size = 2**19  # 0.5MB chunks
        out_file = None
        try:
            offset = 0
            while True:
                try:
                    script, in_data = _bootstrap_powershell_script('winrm_fetch_file.ps1', {
                        'Path': in_path,
                        'BufferSize': buffer_size,
                        'Offset': offset,
                    })
                    display.vvvvv('WINRM FETCH "%s" to "%s" (offset=%d)' % (in_path, out_path, offset), host=self._winrm_host)
                    cmd_parts = _script.get_pwsh_encoded_cmdline(script, override_execution_policy=True)
                    status_code, b_stdout, b_stderr = self._winrm_exec(cmd_parts[0], cmd_parts[1:], stdin_iterator=self._wrapper_payload_stream(in_data))
                    stdout = to_text(b_stdout)
                    stderr = to_text(b_stderr)

                    if status_code != 0:
                        raise OSError(stderr)
                    if stdout.strip() == '[DIR]':
                        data = None
                    else:
                        data = base64.b64decode(stdout.strip())
                    if data is None:
                        break
                    else:
                        if not out_file:
                            # If out_path is a directory and we're expecting a file, bail out now.
                            if os.path.isdir(to_bytes(out_path, errors='surrogate_or_strict')):
                                break
                            out_file = open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb')
                        out_file.write(data)
                        if len(data) < buffer_size:
                            break
                        offset += len(data)
                except Exception:
                    raise AnsibleError('failed to transfer file to "%s"' % to_native(out_path))
        finally:
            if out_file:
                out_file.close()