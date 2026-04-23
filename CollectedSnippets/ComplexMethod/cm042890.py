def _get_memory_info_mb(self) -> Optional[float]:
        pid_str = str(self.pid)
        try:
            if sys.platform == 'darwin': result = subprocess.run(["ps", "-o", "rss=", "-p", pid_str], capture_output=True, text=True, check=True, encoding='utf-8'); return int(result.stdout.strip()) / 1024.0
            elif sys.platform == 'linux':
                with open(f"/proc/{pid_str}/status", encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("VmRSS:"): return int(line.split()[1]) / 1024.0
                return None
            elif sys.platform == 'win32': result = subprocess.run(["tasklist", "/fi", f"PID eq {pid_str}", "/fo", "csv", "/nh"], capture_output=True, text=True, check=True, encoding='cp850', errors='ignore'); parts = result.stdout.strip().split('","'); return int(parts[4].strip().replace('"', '').replace(' K', '').replace(',', '')) / 1024.0 if len(parts) >= 5 else None
            else: return None
        except: return None