def _set_hosts_cache(self, play, refresh=True):
        """Responsible for setting _hosts_cache and _hosts_cache_all

        See comment in ``__init__`` for the purpose of these caches
        """
        if not refresh and all((self._hosts_cache, self._hosts_cache_all)):
            return

        if not play.finalized and TemplateEngine().is_template(play.hosts):
            _pattern = 'all'
        else:
            _pattern = play.hosts or 'all'
        self._hosts_cache_all = [h.name for h in self._inventory.get_hosts(pattern=_pattern, ignore_restrictions=True)]
        self._hosts_cache = [h.name for h in self._inventory.get_hosts(play.hosts, order=play.order)]