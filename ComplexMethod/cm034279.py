def add_host(self, host: str, group: str | None = None, port: int | str | None = None) -> str:
        """Adds a host to inventory and possibly a group if not there already."""

        host = helpers.remove_trust(host)

        if host:
            if not isinstance(host, str):
                raise AnsibleError("Invalid host name supplied, expected a string but got %s for %s" % (type(host), host))

            # TODO: add to_safe_host_name
            g = None
            if group:
                if group in self.groups:
                    g = self.groups[group]
                else:
                    raise AnsibleError("Could not find group %s in inventory" % group)

            if host not in self.hosts:
                h = Host(host, port)
                self.hosts[host] = h
                if self.current_source:  # set to 'first source' in which host was encountered
                    self.set_variable(host, 'inventory_file', self.current_source)
                    self.set_variable(host, 'inventory_dir', basedir(self.current_source))
                else:
                    self.set_variable(host, 'inventory_file', None)
                    self.set_variable(host, 'inventory_dir', None)
                display.debug("Added host %s to inventory" % host)

                # set default localhost from inventory to avoid creating an implicit one. Last localhost defined 'wins'.
                if host in C.LOCALHOST:
                    if self.localhost is None:
                        self.localhost = self.hosts[host]
                        display.vvvv("Set default localhost to %s" % h)
                    else:
                        display.warning("A duplicate localhost-like entry was found (%s). First found localhost was %s" % (h, self.localhost.name))
            else:
                h = self.hosts[host]

            if g:
                g.add_host(h)
                self._groups_dict_cache = {}
                display.debug("Added host %s to group %s" % (host, group))
        else:
            raise AnsibleError("Invalid empty host name provided: %s" % host)

        return host