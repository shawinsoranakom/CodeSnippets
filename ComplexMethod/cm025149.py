async def async_get_component(self) -> ComponentProtocol:
        """Return the component.

        This method will load the component if it's not already loaded
        and will check if import_executor is set and load it in the executor,
        otherwise it will load it in the event loop.
        """
        domain = self.domain
        if domain in (cache := self._cache):
            return cache[domain]

        if self._component_future:
            return await self._component_future

        if debug := _LOGGER.isEnabledFor(logging.DEBUG):
            start = time.perf_counter()

        # Some integrations fail on import because they call functions incorrectly.
        # So we do it before validating config to catch these errors.
        load_executor = self.import_executor and (
            self.pkg_path not in sys.modules
            or (self.config_flow and f"{self.pkg_path}.config_flow" not in sys.modules)
        )
        if not load_executor:
            comp = self._get_component()
            if debug:
                _LOGGER.debug(
                    "Component %s import took %.3f seconds (loaded_executor=False)",
                    self.domain,
                    time.perf_counter() - start,
                )
            return comp

        self._component_future = self.hass.loop.create_future()
        try:
            try:
                comp = await self.hass.async_add_import_executor_job(
                    self._get_component, True
                )
            except ModuleNotFoundError:
                raise
            except ImportError as ex:
                load_executor = False
                _LOGGER.debug(
                    "Failed to import %s in executor", self.domain, exc_info=ex
                )
                # If importing in the executor deadlocks because there is a circular
                # dependency, we fall back to the event loop.
                comp = self._get_component()
            self._component_future.set_result(comp)
        except BaseException as ex:
            self._component_future.set_exception(ex)
            with suppress(BaseException):
                # Set the exception retrieved flag on the future since
                # it will never be retrieved unless there
                # are concurrent calls to async_get_component
                self._component_future.result()
            raise
        finally:
            self._component_future = None

        if debug:
            _LOGGER.debug(
                "Component %s import took %.3f seconds (loaded_executor=%s)",
                self.domain,
                time.perf_counter() - start,
                load_executor,
            )

        return comp