async def _async_setup_platform(
        self,
        async_create_setup_awaitable: Callable[[], Awaitable[None]],
        tries: int = 0,
    ) -> bool:
        """Set up a platform via config file or config entry.

        async_create_setup_awaitable creates an awaitable that sets up platform.
        """
        current_platform.set(self)
        logger = self.logger
        hass = self.hass
        full_name = f"{self.platform_name}.{self.domain}"

        await self.platform_data.async_load_translations()

        logger.info("Setting up %s", full_name)
        warn_task = hass.loop.call_at(
            hass.loop.time() + SLOW_SETUP_WARNING,
            logger.warning,
            "Setup of %s platform %s is taking over %s seconds.",
            self.domain,
            self.platform_name,
            SLOW_SETUP_WARNING,
        )
        try:
            awaitable = async_create_setup_awaitable()
            if asyncio.iscoroutine(awaitable):
                awaitable = create_eager_task(awaitable, loop=hass.loop)

            async with hass.timeout.async_timeout(SLOW_SETUP_MAX_WAIT, self.domain):
                await asyncio.shield(awaitable)

            # Block till all entities are done
            while self._tasks:
                # Await all tasks even if they are done
                # to ensure exceptions are propagated
                pending = self._tasks.copy()
                self._tasks.clear()
                await asyncio.gather(*pending)
        except PlatformNotReady as ex:
            tries += 1
            wait_time = min(tries, 6) * PLATFORM_NOT_READY_BASE_WAIT_TIME
            message = str(ex)
            ready_message = f"ready yet: {message}" if message else "ready yet"
            if tries == 1:
                logger.warning(
                    "Platform %s not %s; Retrying in background in %d seconds",
                    self.platform_name,
                    ready_message,
                    wait_time,
                )
            else:
                logger.debug(
                    "Platform %s not %s; Retrying in %d seconds",
                    self.platform_name,
                    ready_message,
                    wait_time,
                )

            async def setup_again(*_args: Any) -> None:
                """Run setup again."""
                self._async_cancel_retry_setup = None
                await self._async_setup_platform(async_create_setup_awaitable, tries)

            if hass.state is CoreState.running:
                self._async_cancel_retry_setup = async_call_later(
                    hass, wait_time, setup_again
                )
            else:
                self._async_cancel_retry_setup = hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, setup_again
                )
            return False
        except TimeoutError:
            logger.error(
                (
                    "Setup of platform %s is taking longer than %s seconds."
                    " Startup will proceed without waiting any longer."
                ),
                self.platform_name,
                SLOW_SETUP_MAX_WAIT,
            )
            return False
        except (ConfigEntryNotReady, ConfigEntryAuthFailed, ConfigEntryError) as exc:
            _LOGGER.error(
                "%s raises exception %s in forwarded platform "
                "%s; Instead raise %s before calling async_forward_entry_setups",
                self.platform_name,
                type(exc).__name__,
                self.domain,
                type(exc).__name__,
            )
            return False
        except Exception as exc:
            logger.exception(
                "Error while setting up %s platform for %s: %s",
                self.platform_name,
                self.domain,
                exc,  # noqa: TRY401
            )
            return False
        else:
            hass.config.components.add(full_name)
            self._setup_complete = True
            return True
        finally:
            warn_task.cancel()