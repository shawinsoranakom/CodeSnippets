def _get_action_handler_with_module_context(self, templar: TemplateEngine) -> tuple[ActionBase, PluginLoadContext]:
        """
        Returns the correct action plugin to handle the requestion task action and the module context
        """
        module_collection, separator, module_name = self._task.action.rpartition(".")
        module_prefix = module_name.split('_')[0]
        if module_collection:
            # For network modules, which look for one action plugin per platform, look for the
            # action plugin in the same collection as the module by prefixing the action plugin
            # with the same collection.
            network_action = "{0}.{1}".format(module_collection, module_prefix)
        else:
            network_action = module_prefix

        collections = self._task.collections

        # Check if the module has specified an action handler
        module = self._shared_loader_obj.module_loader.find_plugin_with_context(
            self._task.action, collection_list=collections
        )
        if not module.resolved or not module.action_plugin:
            module = None
        if module is not None:
            handler_name = module.action_plugin
        # let action plugin override module, fallback to 'normal' action plugin otherwise
        elif self._shared_loader_obj.action_loader.has_plugin(self._task.action, collection_list=collections):
            handler_name = self._task.action
        elif module_prefix in C.NETWORK_GROUP_MODULES and self._shared_loader_obj.action_loader.has_plugin(network_action, collection_list=collections):
            handler_name = network_action
            display.vvvv("Using network group action {handler} for {action}".format(handler=handler_name,
                                                                                    action=self._task.action),
                         host=self._play_context.remote_addr)
        else:
            # use ansible.legacy.normal to allow (historic) local action_plugins/ override without collections search
            handler_name = 'ansible.legacy.normal'
            collections = None  # until then, we don't want the task's collection list to be consulted; use the builtin

        # networking/psersistent connections handling
        if any(((self._connection.supports_persistence and C.USE_PERSISTENT_CONNECTIONS), self._connection.force_persistence)):

            # check handler in case we dont need to do all the work to setup persistent connection
            handler_class = self._shared_loader_obj.action_loader.get(handler_name, class_only=True)
            if getattr(handler_class, '_requires_connection', True):
                # for persistent connections, initialize socket path and start connection manager
                self._play_context.timeout = self._connection.get_option('persistent_command_timeout')
                display.vvvv('attempting to start connection', host=self._play_context.remote_addr)
                display.vvvv('using connection plugin %s' % self._connection.transport, host=self._play_context.remote_addr)

                options = self._connection.get_options()
                socket_path = start_connection(self._play_context, options, self._task._uuid)
                display.vvvv('local domain socket path is %s' % socket_path, host=self._play_context.remote_addr)
                setattr(self._connection, '_socket_path', socket_path)
            else:
                # TODO: set self._connection to dummy/noop connection, using local for now
                self._connection = self._get_connection({}, templar, 'local')

        handler = self._shared_loader_obj.action_loader.get(
            handler_name,
            task=self._task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=Templar._from_template_engine(templar),
            shared_loader_obj=self._shared_loader_obj,
            collection_list=collections
        )

        if not handler:
            raise AnsibleError("the handler '%s' was not found" % handler_name)

        return handler, module