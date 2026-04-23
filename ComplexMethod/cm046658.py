def visit_Call(self, node):
            func = node.func
            func_name = None
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    if func.value.id in self.signal_aliases:
                        func_name = f"signal.{func.attr}"
            elif isinstance(func, ast.Name):
                if func.id in ("signal", "setitimer", "alarm", "pthread_sigmask"):
                    func_name = func.id

            if func_name:
                if func_name in ("signal.signal", "signal"):
                    if len(node.args) >= 1:
                        if _ast_name_matches(
                            node.args[0], ("SIGALRM", "signal.SIGALRM")
                        ):
                            signal_tampering.append(
                                {
                                    "type": "signal_handler_override",
                                    "line": node.lineno,
                                    "description": "Overrides SIGALRM handler",
                                }
                            )
                elif func_name in ("signal.setitimer", "setitimer"):
                    if len(node.args) >= 1:
                        if _ast_name_matches(
                            node.args[0], ("ITIMER_REAL", "signal.ITIMER_REAL")
                        ):
                            signal_tampering.append(
                                {
                                    "type": "timer_manipulation",
                                    "line": node.lineno,
                                    "description": "Manipulates ITIMER_REAL timer",
                                }
                            )
                elif func_name in ("signal.alarm", "alarm"):
                    signal_tampering.append(
                        {
                            "type": "alarm_manipulation",
                            "line": node.lineno,
                            "description": "Manipulates alarm timer",
                        }
                    )
                elif func_name in ("signal.pthread_sigmask", "pthread_sigmask"):
                    signal_tampering.append(
                        {
                            "type": "signal_mask",
                            "line": node.lineno,
                            "description": "Modifies signal mask (may block SIGALRM)",
                        }
                    )

            # --- Shell escape detection ---
            # Resolve the fully qualified function name for os.*/subprocess.*
            shell_func = None
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    if func.value.id in self.os_aliases:
                        shell_func = f"os.{func.attr}"
                    elif func.value.id in self.subprocess_aliases:
                        shell_func = f"subprocess.{func.attr}"
            elif isinstance(func, ast.Name):
                # Check from-import aliases: from os import system; system(...)
                shell_func = self.shell_exec_aliases.get(func.id)

            if shell_func and shell_func in _SHELL_EXEC_FUNCS:
                # Expand **kwargs dicts to inspect their keys
                expanded_kwargs: dict[str, ast.AST] = {}
                has_opaque_kwargs = False
                for kw in node.keywords:
                    if kw.arg is not None:
                        expanded_kwargs[kw.arg] = kw.value
                    elif isinstance(kw.value, ast.Dict):
                        for k, v in zip(kw.value.keys, kw.value.values):
                            key = _extract_string_from_node(k) if k else None
                            if key is not None:
                                expanded_kwargs[key] = v
                    else:
                        has_opaque_kwargs = True

                cmd_kw_values = [
                    v for k, v in expanded_kwargs.items() if k in _CMD_KWARGS
                ]
                all_call_args = list(node.args) + cmd_kw_values
                blocked_in_args = _check_args_for_blocked(all_call_args)

                if has_opaque_kwargs:
                    # Can't inspect dynamic **kwargs -- flag as unsafe
                    shell_escapes.append(
                        {
                            "type": "shell_escape_dynamic",
                            "line": node.lineno,
                            "description": (
                                f"{shell_func}() called with dynamic **kwargs"
                            ),
                        }
                    )
                elif blocked_in_args:
                    shell_escapes.append(
                        {
                            "type": "shell_escape",
                            "line": node.lineno,
                            "description": (
                                f"{shell_func}() invokes blocked command(s): "
                                f"{', '.join(sorted(blocked_in_args))}"
                            ),
                        }
                    )
                else:
                    # Only flag dynamic args for functions that interpret
                    # strings as shell commands, or when shell= might be
                    # enabled.  Treat any non-literal-False shell= value
                    # as potentially True (conservative).
                    _STRING_SHELL_FUNCS = frozenset(
                        {
                            "os.system",
                            "os.popen",
                            "os.popen2",
                            "os.popen3",
                            "os.popen4",
                            "subprocess.getoutput",
                            "subprocess.getstatusoutput",
                        }
                    )
                    shell_node = expanded_kwargs.get("shell")
                    shell_safe = shell_node is None or (
                        isinstance(shell_node, ast.Constant)
                        and shell_node.value is False
                    )
                    if shell_func in _STRING_SHELL_FUNCS or not shell_safe:

                        def _is_safe_literal(n):
                            if _extract_string_from_node(n) is not None:
                                return True
                            if isinstance(n, (ast.List, ast.Tuple)):
                                return all(
                                    _extract_string_from_node(e) is not None
                                    for e in n.elts
                                )
                            return False

                        has_non_literal = any(
                            not _is_safe_literal(a) for a in all_call_args
                        )
                        if has_non_literal:
                            shell_escapes.append(
                                {
                                    "type": "shell_escape_dynamic",
                                    "line": node.lineno,
                                    "description": (
                                        f"{shell_func}() called with non-literal "
                                        f"shell command (potential shell escape)"
                                    ),
                                }
                            )

            self.generic_visit(node)