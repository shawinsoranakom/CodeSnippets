async def _listen_windows(self, user_done_event, check_browser_process, tag: str):
        """Windows-specific keyboard listener using msvcrt."""
        try:
            import msvcrt
        except ImportError:
            raise ImportError("msvcrt module not available on this platform")

        while True:
            try:
                # Check for keyboard input
                if msvcrt.kbhit():
                    raw = msvcrt.getch()

                    # Handle Unicode decoding more robustly
                    key = None
                    try:
                        key = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            # Try different encodings
                            key = raw.decode("latin1")
                        except UnicodeDecodeError:
                            # Skip if we can't decode
                            continue

                    # Validate key
                    if not key or len(key) != 1:
                        continue

                    # Check for printable characters only
                    if not key.isprintable():
                        continue

                    # Check for quit command
                    if key.lower() == "q":
                        self.logger.info(
                            self._get_quit_message(tag),
                            tag=tag,
                            base_color=LogColor.GREEN
                        )
                        user_done_event.set()
                        return

                # Check if browser process ended
                if await check_browser_process():
                    return

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.warning(f"Error in Windows keyboard listener: {e}", tag=tag)
                # Continue trying instead of failing completely
                await asyncio.sleep(0.1)
                continue