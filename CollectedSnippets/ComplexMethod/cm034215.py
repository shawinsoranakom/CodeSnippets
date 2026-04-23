def run(self):

        super(GalaxyCLI, self).run()

        self.galaxy = Galaxy()

        # dynamically add per server config depending on declared servers
        C.config.load_galaxy_server_defs(C.GALAXY_SERVER_LIST)

        galaxy_options = {}
        for optional_key in ['clear_response_cache', 'no_cache']:
            if optional_key in context.CLIARGS:
                galaxy_options[optional_key] = context.CLIARGS[optional_key]

        config_servers = []
        # Need to filter out empty strings or non truthy values as an empty server list env var is equal to [''].
        server_list = [s for s in C.GALAXY_SERVER_LIST or [] if s]
        for server_priority, server_key in enumerate(server_list, start=1):

            # resolve the config created options above with existing config and user options
            server_options = C.config.get_plugin_options(plugin_type='galaxy_server', name=server_key)

            # auth_url is used to create the token, but not directly by GalaxyAPI, so
            # it doesn't need to be passed as kwarg to GalaxyApi, same for others we pop here
            auth_url = server_options.pop('auth_url')
            client_id = server_options.pop('client_id')
            client_secret = server_options.pop('client_secret')
            token_val = server_options['token'] or NoTokenSentinel
            username = server_options['username']
            if server_options['validate_certs'] is None:
                server_options['validate_certs'] = context.CLIARGS['resolved_validate_certs']
            validate_certs = server_options['validate_certs']

            # default case if no auth info is provided.
            server_options['token'] = None

            if username:
                server_options['token'] = BasicAuthToken(username, server_options['password'])
            else:
                if auth_url:
                    server_options['token'] = KeycloakToken(
                        access_token=token_val,
                        auth_url=auth_url,
                        validate_certs=validate_certs,
                        client_id=client_id,
                        client_secret=client_secret,
                    )
                elif token_val:
                    # The galaxy v1 / github / django / 'Token'
                    server_options['token'] = GalaxyToken(token=token_val)

            server_options.update(galaxy_options)
            config_servers.append(GalaxyAPI(
                self.galaxy, server_key,
                priority=server_priority,
                **server_options
            ))

        cmd_server = context.CLIARGS['api_server']

        cmd_token = GalaxyToken(token=context.CLIARGS['api_key'])

        validate_certs = context.CLIARGS['resolved_validate_certs']
        default_server_timeout = context.CLIARGS['timeout'] if context.CLIARGS['timeout'] is not None else C.GALAXY_SERVER_TIMEOUT
        if cmd_server:
            # Cmd args take precedence over the config entry but fist check if the arg was a name and use that config
            # entry, otherwise create a new API entry for the server specified.
            config_server = next((s for s in config_servers if s.name == cmd_server), None)
            if config_server:
                self.api_servers.append(config_server)
            else:
                self.api_servers.append(GalaxyAPI(
                    self.galaxy, 'cmd_arg', cmd_server, token=cmd_token,
                    priority=len(config_servers) + 1,
                    validate_certs=validate_certs,
                    timeout=default_server_timeout,
                    **galaxy_options
                ))
        else:
            self.api_servers = config_servers

        # Default to C.GALAXY_SERVER if no servers were defined
        if len(self.api_servers) == 0:
            self.api_servers.append(GalaxyAPI(
                self.galaxy, 'default', C.GALAXY_SERVER, token=cmd_token,
                priority=0,
                validate_certs=validate_certs,
                timeout=default_server_timeout,
                **galaxy_options
            ))

        # checks api versions once a GalaxyRole makes an api call
        # self.api can be used to evaluate the best server immediately
        self.lazy_role_api = RoleDistributionServer(None, self.api_servers)

        return context.CLIARGS['func']()