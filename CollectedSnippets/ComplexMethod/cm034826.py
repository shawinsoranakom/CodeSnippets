def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level > 0:
            raise ImportError(
                "Relative imports are not allowed inside a .pa.py sandbox."
            )
        base = name.split(".")[0]
        if base not in allowed:
            raise ImportError(
                f"Import of '{name}' is not allowed in safe execution mode.\n"
                f"Allowed top-level modules: {', '.join(sorted(allowed))}"
            )
        # Explicit allowlist takes priority over the blocklist below.
        # This permits e.g. "g4f.Provider.helper" even though "g4f.Provider"
        # is blocked.
        for allowed_sub in _ALLOWED_G4F_SUBPATHS:
            if name == allowed_sub or name.startswith(allowed_sub + "."):
                return original(name, globals, locals, fromlist, level)
        # Block sensitive g4f submodules even though g4f itself is allowed.
        if name in _BLOCKED_SUBMODULES:
            raise ImportError(
                f"Import of '{name}' is not allowed inside a .pa.py sandbox "
                f"for security reasons."
            )
        # Also block when a blocked submodule is the parent of a deeper import
        # (e.g. "g4f.tools.auth.something", "g4f.Provider.OpenAI").
        for blocked in _BLOCKED_SUBMODULES:
            if name.startswith(blocked + "."):
                raise ImportError(
                    f"Import of '{name}' is not allowed inside a .pa.py sandbox "
                    f"for security reasons."
                )
        return original(name, globals, locals, fromlist, level)