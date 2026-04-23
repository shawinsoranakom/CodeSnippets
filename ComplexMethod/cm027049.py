async def async_ping(self) -> dict[str, Any] | None:
        """Send ICMP echo request and return details if success."""
        _LOGGER.debug(
            "Pinging %s with: `%s`", self.ip_address, " ".join(self._ping_cmd)
        )

        pinger = await asyncio.create_subprocess_exec(
            *self._ping_cmd,
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            close_fds=False,  # required for posix_spawn
        )
        try:
            async with asyncio.timeout(self._count + PING_TIMEOUT):
                out_data, out_error = await pinger.communicate()

            if out_data:
                _LOGGER.debug(
                    "Output of command: `%s`, return code: %s:\n%s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                    out_data,
                )
            if out_error:
                _LOGGER.debug(
                    "Error of command: `%s`, return code: %s:\n%s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                    out_error,
                )

            if pinger.returncode and pinger.returncode > 1:
                # returncode of 1 means the host is unreachable
                _LOGGER.exception(
                    "Error running command: `%s`, return code: %s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                )

            if "max/" not in str(out_data):
                match = PING_MATCHER_BUSYBOX.search(
                    str(out_data).rsplit("\n", maxsplit=1)[-1]
                )
                if TYPE_CHECKING:
                    assert match is not None
                rtt_min, rtt_avg, rtt_max = match.groups()
                return {"min": rtt_min, "avg": rtt_avg, "max": rtt_max}
            match = PING_MATCHER.search(str(out_data).rsplit("\n", maxsplit=1)[-1])
            if TYPE_CHECKING:
                assert match is not None
            rtt_min, rtt_avg, rtt_max, rtt_mdev = match.groups()
        except TimeoutError:
            _LOGGER.debug(
                "Timed out running command: `%s`, after: %s",
                " ".join(self._ping_cmd),
                self._count + PING_TIMEOUT,
            )

            if pinger:
                with suppress(TypeError, ProcessLookupError):
                    pinger.kill()
                del pinger

            return None
        except AttributeError as err:
            _LOGGER.debug("Error matching ping output: %s", err)
            return None
        return {"min": rtt_min, "avg": rtt_avg, "max": rtt_max, "mdev": rtt_mdev}