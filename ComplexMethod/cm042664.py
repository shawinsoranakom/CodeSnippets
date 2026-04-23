def _apply_settings(self) -> None:
        if self.settings.frozen:
            return

        self.addons.load_settings(self.settings)
        self.stats = load_object(self.settings["STATS_CLASS"])(self)

        lf_cls: type[LogFormatter] = load_object(self.settings["LOG_FORMATTER"])
        self.logformatter = lf_cls.from_crawler(self)

        self.request_fingerprinter = build_from_crawler(
            load_object(self.settings["REQUEST_FINGERPRINTER_CLASS"]),
            self,
        )

        use_reactor = self.settings.getbool("TWISTED_REACTOR_ENABLED")
        if use_reactor:
            # We either install a reactor or expect one to be installed.
            reactor_class: str = self.settings["TWISTED_REACTOR"]
            event_loop: str = self.settings["ASYNCIO_EVENT_LOOP"]
            if self._init_reactor:
                # We need to install a reactor.
                # This needs to be done after the spider settings are merged,
                # but before something imports twisted.internet.reactor.
                if reactor_class:
                    # Install a specific reactor.
                    install_reactor(reactor_class, event_loop)
                else:
                    # Install the default one.
                    from twisted.internet import reactor  # noqa: F401
            elif not is_reactor_installed():
                # We need a reactor to be already installed.
                raise RuntimeError(
                    "We expected a Twisted reactor to be installed but it isn't."
                )
            if reactor_class:
                # We need to check that the correct reactor is installed.
                verify_installed_reactor(reactor_class)
                if is_asyncio_reactor_installed() and event_loop:
                    verify_installed_asyncio_event_loop(event_loop)

            if self._init_reactor or reactor_class:
                log_reactor_info()
        else:
            # We expect a reactor to not be installed.
            if is_reactor_installed():
                raise RuntimeError(
                    "TWISTED_REACTOR_ENABLED is False but a Twisted reactor is installed."
                )
            logger.debug("Not using a Twisted reactor")
            self._apply_reactorless_default_settings()

        self.extensions = ExtensionManager.from_crawler(self)
        self.settings.freeze()

        d = dict(overridden_settings(self.settings))
        logger.info(
            "Overridden settings:\n%(settings)s", {"settings": pprint.pformat(d)}
        )