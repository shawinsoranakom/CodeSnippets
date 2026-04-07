def _router_func(action):
        def _route_db(self, model, **hints):
            chosen_db = None
            for router in self.routers:
                try:
                    method = getattr(router, action)
                except AttributeError:
                    # If the router doesn't have a method, skip to the next
                    # one.
                    pass
                else:
                    chosen_db = method(model, **hints)
                    if chosen_db:
                        return chosen_db
            instance = hints.get("instance")
            if instance is not None and instance._state.db:
                return instance._state.db
            return DEFAULT_DB_ALIAS

        return _route_db