def _is_in_script_thread(self) -> bool:
        """True if the calling function is running in the script thread"""
        return self._script_thread == threading.current_thread()