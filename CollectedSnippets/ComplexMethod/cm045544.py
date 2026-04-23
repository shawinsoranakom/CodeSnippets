async def cleanup(self) -> None:
        """Cleans up sandbox resources."""
        errors = []
        try:
            if self.terminal:
                try:
                    await self.terminal.close()
                except Exception as e:
                    errors.append(f"Terminal cleanup error: {e}")
                finally:
                    self.terminal = None

            if self.container:
                try:
                    await asyncio.to_thread(self.container.stop, timeout=5)
                except Exception as e:
                    errors.append(f"Container stop error: {e}")

                try:
                    await asyncio.to_thread(self.container.remove, force=True)
                except Exception as e:
                    errors.append(f"Container remove error: {e}")
                finally:
                    self.container = None

        except Exception as e:
            errors.append(f"General cleanup error: {e}")

        if errors:
            print(f"Warning: Errors during cleanup: {', '.join(errors)}")