def _dlclose(self) -> None:
        f_dlclose = None
        # During Python interpreter shutdown, importing modules or calling
        # dlclose is unsafe. Silently skip cleanup in that case.
        try:
            import sys

            if sys.is_finalizing():
                return
        except Exception:
            # import machinery may already be torn down
            return
        if is_linux():
            syms = CDLL(None)
            if not hasattr(syms, "dlclose"):
                # Apline Linux
                syms = CDLL("libc.so")

            if hasattr(syms, "dlclose"):
                f_dlclose = syms.dlclose
        elif is_windows():
            import ctypes

            kernel32 = ctypes.CDLL("kernel32", use_last_error=True)

            f_dlclose = kernel32.FreeLibrary
        else:
            raise NotImplementedError("Unsupported env, failed to do dlclose!")

        if f_dlclose is not None:
            if is_linux():
                f_dlclose.argtypes = [c_void_p]
                f_dlclose(self.DLL._handle)
            elif is_windows():
                import ctypes
                from ctypes import wintypes

                f_dlclose.argtypes = [wintypes.HMODULE]
                f_dlclose(self.DLL._handle)
        else:
            log.warning(
                "dll unloading function was not found, library may not be unloaded properly!"
            )