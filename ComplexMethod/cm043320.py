async def _listen_unix(self, user_done_event: asyncio.Event, check_browser_process, tag: str):
        """Unix/Linux/macOS keyboard listener using termios and select."""
        try:
            import termios
            import tty
            import select
        except ImportError:
            raise ImportError("termios/tty/select modules not available on this platform")

        # Get stdin file descriptor
        try:
            fd = sys.stdin.fileno()
        except (AttributeError, OSError):
            raise ImportError("stdin is not a terminal")

        # Save original terminal settings
        old_settings = None
        try:
            old_settings = termios.tcgetattr(fd)
        except termios.error as e:
            raise ImportError(f"Cannot get terminal attributes: {e}")

        try:
            # Switch to non-canonical mode (cbreak mode)
            tty.setcbreak(fd)

            while True:
                try:
                    # Use select to check if input is available (non-blocking)
                    # Timeout of 0.5 seconds to periodically check browser process
                    readable, _, _ = select.select([sys.stdin], [], [], 0.5)

                    if readable:
                        # Read one character
                        key = sys.stdin.read(1)

                        if key and key.lower() == "q":
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

                except (KeyboardInterrupt, EOFError):
                    # Handle Ctrl+C or EOF gracefully
                    self.logger.info("Keyboard interrupt received", tag=tag)
                    user_done_event.set()
                    return
                except Exception as e:
                    self.logger.warning(f"Error in Unix keyboard listener: {e}", tag=tag)
                    await asyncio.sleep(0.1)
                    continue

        finally:
            # Always restore terminal settings
            if old_settings is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except Exception as e:
                    self.logger.error(f"Failed to restore terminal settings: {e}", tag=tag)