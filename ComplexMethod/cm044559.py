def _bind_unbind_keys(self):
        """ Bind or unbind this editor's hotkeys depending on whether it is active. """
        unbind_keys = [key for key, binding in self.key_bindings.items()
                       if binding["bound_to"] is not None
                       and binding["bound_to"] != self.selected_action]
        for key in unbind_keys:
            logger.debug("Unbinding key '%s'", key)
            self.winfo_toplevel().unbind(key)
            self.key_bindings[key]["bound_to"] = None

        bind_keys = {key: binding[self.selected_action]
                     for key, binding in self.key_bindings.items()
                     if self.selected_action in binding
                     and binding["bound_to"] != self.selected_action}
        for key, method in bind_keys.items():
            logger.debug("Binding key '%s' to method %s", key, method)
            self.winfo_toplevel().bind(key, method)
            self.key_bindings[key]["bound_to"] = self.selected_action