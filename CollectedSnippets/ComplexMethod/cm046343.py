def name() -> str:
        """Return a normalized CPU model string from platform-specific sources."""
        try:
            if sys.platform == "darwin":
                # Query macOS sysctl for the CPU brand string
                s = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
                ).stdout.strip()
                if s:
                    return CPUInfo._clean(s)
            elif sys.platform.startswith("linux"):
                # Parse /proc/cpuinfo for the first "model name" entry
                p = Path("/proc/cpuinfo")
                if p.exists():
                    for line in p.read_text(errors="ignore").splitlines():
                        if "model name" in line:
                            return CPUInfo._clean(line.split(":", 1)[1])
            elif sys.platform.startswith("win"):
                try:
                    import winreg as wr

                    with wr.OpenKey(wr.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                        val, _ = wr.QueryValueEx(k, "ProcessorNameString")
                        if val:
                            return CPUInfo._clean(val)
                except Exception:
                    # Fall through to generic platform fallbacks on Windows registry access failure
                    pass
            # Generic platform fallbacks
            s = platform.processor() or getattr(platform.uname(), "processor", "") or platform.machine()
            return CPUInfo._clean(s or "Unknown CPU")
        except Exception:
            # Ensure a string is always returned even on unexpected failures
            s = platform.processor() or platform.machine() or ""
            return CPUInfo._clean(s or "Unknown CPU")