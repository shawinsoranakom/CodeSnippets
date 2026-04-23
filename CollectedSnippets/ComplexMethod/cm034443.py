def get_systemd_status_dict(self):

        # Check status first as show will not fail if service does not exist
        (rc, out, err) = self.execute_command("%s show '%s'" % (self.enable_cmd, self.__systemd_unit,))
        if rc != 0:
            self.module.fail_json(msg='failure %d running systemctl show for %r: %s' % (rc, self.__systemd_unit, err))
        elif 'LoadState=not-found' in out:
            self.module.fail_json(msg='systemd could not find the requested service "%r": %s' % (self.__systemd_unit, err))

        key = None
        value_buffer = []
        status_dict = {}
        for line in out.splitlines():
            if '=' in line:
                if not key:
                    key, value = line.split('=', 1)
                    # systemd fields that are shell commands can be multi-line
                    # We take a value that begins with a "{" as the start of
                    # a shell command and a line that ends with "}" as the end of
                    # the command
                    if value.lstrip().startswith('{'):
                        if value.rstrip().endswith('}'):
                            status_dict[key] = value
                            key = None
                        else:
                            value_buffer.append(value)
                    else:
                        status_dict[key] = value
                        key = None
                else:
                    if line.rstrip().endswith('}'):
                        status_dict[key] = '\n'.join(value_buffer)
                        key = None
                    else:
                        value_buffer.append(value)
            else:
                value_buffer.append(value)

        return status_dict