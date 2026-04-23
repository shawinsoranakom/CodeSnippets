async def async_get_platforms(
        self, platform_names: Iterable[Platform | str]
    ) -> dict[str, ModuleType]:
        """Return a platforms for an integration."""
        domain = self.domain
        platforms: dict[str, ModuleType] = {}

        load_executor_platforms: list[str] = []
        load_event_loop_platforms: list[str] = []
        in_progress_imports: dict[str, asyncio.Future[ModuleType]] = {}
        import_futures: list[tuple[str, asyncio.Future[ModuleType]]] = []

        for platform_name in platform_names:
            if platform := self._get_platform_cached_or_raise(platform_name):
                platforms[platform_name] = platform
                continue

            # Another call to async_get_platforms is already importing this platform
            if future := self._import_futures.get(platform_name):
                in_progress_imports[platform_name] = future
                continue

            full_name = f"{domain}.{platform_name}"
            if (
                self.import_executor
                and full_name not in self.hass.config.components
                and f"{self.pkg_path}.{platform_name}" not in sys.modules
            ):
                load_executor_platforms.append(platform_name)
            else:
                load_event_loop_platforms.append(platform_name)

            import_future = self.hass.loop.create_future()
            self._import_futures[platform_name] = import_future
            import_futures.append((platform_name, import_future))

        if load_executor_platforms or load_event_loop_platforms:
            if debug := _LOGGER.isEnabledFor(logging.DEBUG):
                start = time.perf_counter()

            try:
                if load_executor_platforms:
                    try:
                        platforms.update(
                            await self.hass.async_add_import_executor_job(
                                self._load_platforms, platform_names
                            )
                        )
                    except ModuleNotFoundError:
                        raise
                    except ImportError as ex:
                        _LOGGER.debug(
                            "Failed to import %s platforms %s in executor",
                            domain,
                            load_executor_platforms,
                            exc_info=ex,
                        )
                        # If importing in the executor deadlocks because there is a circular
                        # dependency, we fall back to the event loop.
                        load_event_loop_platforms.extend(load_executor_platforms)

                if load_event_loop_platforms:
                    platforms.update(self._load_platforms(platform_names))

                for platform_name, import_future in import_futures:
                    import_future.set_result(platforms[platform_name])

            except BaseException as ex:
                for _, import_future in import_futures:
                    import_future.set_exception(ex)
                    with suppress(BaseException):
                        # Set the exception retrieved flag on the future since
                        # it will never be retrieved unless there
                        # are concurrent calls to async_get_platforms
                        import_future.result()
                raise

            finally:
                for platform_name, _ in import_futures:
                    self._import_futures.pop(platform_name)

                if debug:
                    _LOGGER.debug(
                        "Importing platforms for %s executor=%s loop=%s took %.2fs",
                        domain,
                        load_executor_platforms,
                        load_event_loop_platforms,
                        time.perf_counter() - start,
                    )

        if in_progress_imports:
            for platform_name, future in in_progress_imports.items():
                platforms[platform_name] = await future

        return platforms