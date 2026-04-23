def test_no_non_trivial_thread_locals(self):
        """Scan c10d sources for thread_local with non-trivial destructors."""
        c10d_dir = self._c10d_src_dir()
        self.assertTrue(
            c10d_dir.is_dir(),
            f"c10d source directory not found: {c10d_dir}",
        )

        violations = []
        for ext in ("*.cpp", "*.hpp", "*.h", "*.cc"):
            for filepath in c10d_dir.rglob(ext):
                lines = filepath.read_text().splitlines()
                idx = 0
                while idx < len(lines):
                    stripped = lines[idx].strip()
                    idx += 1
                    # Skip pure comments and static_assert guards
                    if (
                        stripped.startswith(("//", "/*"))
                        or "static_assert" in stripped
                        or "thread_local" not in stripped
                    ):
                        continue
                    # Try single-line match first
                    m = _TLS_DECL_RE.search(stripped)
                    if not m and idx < len(lines):
                        # Multi-line declaration (type on one line,
                        # variable name on the next)
                        combined = stripped + " " + lines[idx].strip()
                        m = _TLS_DECL_RE.search(combined)
                    if not m:
                        continue
                    tls_type, var_name = m.group(1), m.group(2)
                    if self._is_safe_type(tls_type):
                        continue
                    rel = str(filepath.relative_to(c10d_dir))
                    # Strip class qualifiers from var_name for allowlist
                    # e.g. "Foo<T>::bar" -> "bar"
                    bare_name = var_name.rsplit("::", 1)[-1]
                    if (rel, bare_name) in self._KNOWN_VIOLATIONS:
                        continue
                    violations.append(
                        f"  {rel}:{idx}: thread_local {tls_type} {var_name}"
                    )

        self.assertEqual(
            violations,
            [],
            "Non-trivially-destructible thread_local variable(s) found in c10d.\n"
            "These cause fork-deadlocks via __cxa_thread_atexit.\n"
            "Use a raw pointer (T*) with lazy heap-allocation instead.\n\n"
            "Violations:\n" + "\n".join(violations),
        )