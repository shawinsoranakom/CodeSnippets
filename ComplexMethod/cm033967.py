def search_handlers_by_notification(self, notification: str, iterator: PlayIterator) -> t.Generator[Handler, None, None]:
        handlers = [h for b in reversed(iterator._play.handlers) for h in b.block]
        # iterate in reversed order since last handler loaded with the same name wins
        for handler in handlers:
            if not handler.name:
                continue

            if not handler.cached_name:
                def variables_factory() -> dict[str, t.Any]:
                    return self._variable_manager.get_vars(
                        play=iterator._play,
                        task=handler,
                        _hosts=self._hosts_cache,
                        _hosts_all=self._hosts_cache_all
                    )

                templar = TemplateEngine(variables_factory=variables_factory)

                try:
                    handler.name = templar.template(handler.name)
                except AnsibleTemplateError as e:
                    # We skip this handler due to the fact that it may be using
                    # a variable in the name that was conditionally included via
                    # set_fact or some other method, and we don't want to error
                    # out unnecessarily
                    if not handler.listen:
                        display.warning(
                            "Handler '%s' is unusable because it has no listen topics and "
                            "the name could not be templated (host-specific variables are "
                            "not supported in handler names). The error: %s" % (handler.name, to_text(e))
                        )
                    continue

                handler.cached_name = True

            # first we check with the full result of get_name(), which may
            # include the role name (if the handler is from a role). If that
            # is not found, we resort to the simple name field, which doesn't
            # have anything extra added to it.
            if notification in {
                handler.name,
                handler.get_name(include_role_fqcn=False),
                handler.get_name(include_role_fqcn=True),
            }:
                yield handler
                break

        seen = set()
        for handler in handlers:
            if notification in handler.listen:
                if handler.name and handler.name in seen:
                    continue
                seen.add(handler.name)
                yield handler