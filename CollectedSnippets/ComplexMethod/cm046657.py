def visit_ImportFrom(self, node):
            if node.module == "signal":
                self.imports_signal = True
                for alias in node.names:
                    if alias.name in (
                        "signal",
                        "SIGALRM",
                        "SIG_IGN",
                        "setitimer",
                        "ITIMER_REAL",
                        "pthread_sigmask",
                        "SIG_BLOCK",
                        "alarm",
                    ):
                        self.signal_aliases.add(alias.asname or alias.name)
            elif node.module in ("os", "subprocess"):
                if node.module == "os":
                    self.os_aliases.add("os")
                else:
                    self.subprocess_aliases.add("subprocess")
                # Track from-imports of dangerous functions
                for alias in node.names:
                    fq = f"{node.module}.{alias.name}"
                    if fq in _SHELL_EXEC_FUNCS:
                        self.shell_exec_aliases[alias.asname or alias.name] = fq
            self.generic_visit(node)