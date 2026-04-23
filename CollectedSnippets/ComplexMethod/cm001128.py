async def scan_file(
        self, content: bytes, *, filename: str = "unknown"
    ) -> VirusScanResult:
        """
        Scan `content`.  Returns a result object or raises on infrastructure
        failure (unreachable daemon, etc.).
        The algorithm always tries whole-file first. If the daemon refuses
        on size grounds, it falls back to chunked parallel scanning.
        """
        if not self.settings.clamav_service_enabled:
            logger.warning(f"Virus scanning disabled – accepting {filename}")
            return VirusScanResult(
                is_clean=True, scan_time_ms=0, file_size=len(content)
            )
        if len(content) == 0:
            logger.debug(f"Skipping virus scan for empty file {filename}")
            return VirusScanResult(is_clean=True, scan_time_ms=0, file_size=0)
        if len(content) > self.settings.max_scan_size:
            logger.warning(
                f"File {filename} ({len(content)} bytes) exceeds client max scan size ({self.settings.max_scan_size}); Stopping virus scan"
            )
            return VirusScanResult(
                is_clean=self.settings.mark_failed_scans_as_clean,
                file_size=len(content),
                scan_time_ms=0,
            )

        # Ensure daemon is reachable (small RTT check)
        if not await self._client.ping():
            raise RuntimeError("ClamAV service is unreachable")

        start = time.monotonic()
        chunk_size = max(1, len(content))  # Start with full content length
        for retry in range(self.settings.max_retries):
            # For small files, don't check min_chunk_size limit
            if chunk_size < self.settings.min_chunk_size and chunk_size < len(content):
                break
            logger.debug(
                f"Scanning {filename} with chunk size: {chunk_size // 1_048_576} MB (retry {retry + 1}/{self.settings.max_retries})"
            )
            try:
                tasks = [
                    asyncio.create_task(self._instream(content[o : o + chunk_size]))
                    for o in range(0, len(content), chunk_size)
                ]
                for coro in asyncio.as_completed(tasks):
                    infected, threat = await coro
                    if infected:
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        return VirusScanResult(
                            is_clean=False,
                            threat_name=threat,
                            file_size=len(content),
                            scan_time_ms=int((time.monotonic() - start) * 1000),
                        )
                # All chunks clean
                return VirusScanResult(
                    is_clean=True,
                    file_size=len(content),
                    scan_time_ms=int((time.monotonic() - start) * 1000),
                )
            except RuntimeError as exc:
                if str(exc) == "size-limit":
                    chunk_size //= 2
                    continue
                logger.error(f"Cannot scan {filename}: {exc}")
                raise
        # Phase 3 – give up but warn
        logger.warning(
            f"Unable to virus scan {filename} ({len(content)} bytes) even with minimum chunk size ({self.settings.min_chunk_size} bytes). Recommend manual review."
        )
        return VirusScanResult(
            is_clean=self.settings.mark_failed_scans_as_clean,
            file_size=len(content),
            scan_time_ms=int((time.monotonic() - start) * 1000),
        )