def write(self, vals):
        """Ensure we cannot archive a server in-use"""
        usages_per_server = {}
        if not vals.get('active', True):
            usages_per_server = self._active_usages_compute()

        if not usages_per_server:
            return super().write(vals)

        # Write cannot be performed as some server are used, build detailed usage per server
        usage_details_per_server = {}
        is_multiple_server_usage = len(usages_per_server) > 1
        for server in self:
            if server.id not in usages_per_server:
                continue
            usage_details = []
            if is_multiple_server_usage:
                usage_details.append(_('%s (Dedicated Outgoing Mail Server):', server.display_name))
            usage_details.extend(map(lambda u: f'- {u}', usages_per_server[server.id]))
            usage_details_per_server[server] = usage_details

        # Raise the error with the ordered list of servers and concatenated detailed usages
        servers_ordered_by_name = sorted(usage_details_per_server.keys(), key=lambda r: r.display_name)
        error_server_usage = ', '.join(server.display_name for server in servers_ordered_by_name)
        error_usage_details = '\n'.join(line
                                        for server in servers_ordered_by_name
                                        for line in usage_details_per_server[server])
        if is_multiple_server_usage:
            raise UserError(
                _('You cannot archive these Outgoing Mail Servers (%(server_usage)s) because they are still used in the following case(s):\n%(usage_details)s',
                  server_usage=error_server_usage, usage_details=error_usage_details))
        raise UserError(
            _('You cannot archive this Outgoing Mail Server (%(server_usage)s) because it is still used in the following case(s):\n%(usage_details)s',
              server_usage=error_server_usage, usage_details=error_usage_details))