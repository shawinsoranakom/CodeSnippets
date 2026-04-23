def runsource(self, source, filename="<input>", symbol="single"):
        try:
            tree = self.compile.compiler(
                source,
                filename,
                "exec",
                ast.PyCF_ONLY_AST,
                incomplete_input=False,
            )
        except SyntaxError as e:
            # If it looks like pip install was entered (a common beginner
            # mistake), provide a hint to use the system command prompt.
            if re.match(r"^\s*(pip3?|py(thon3?)? -m pip) install.*", source):
                e.add_note(
                    "The Python package manager (pip) can only be used"
                    " outside of the Python REPL.\n"
                    "Try the 'pip' command in a separate terminal or"
                    " command prompt."
                )
            self.showsyntaxerror(filename, source=source)
            return False
        except (OverflowError, ValueError):
            self.showsyntaxerror(filename, source=source)
            return False
        if tree.body:
            *_, last_stmt = tree.body
        for stmt in tree.body:
            wrapper = ast.Interactive if stmt is last_stmt else ast.Module
            the_symbol = symbol if stmt is last_stmt else "exec"
            item = wrapper([stmt])
            try:
                code = self.compile.compiler(item, filename, the_symbol)
                linecache._register_code(code, source, filename)
            except SyntaxError as e:
                if e.args[0] == "'await' outside function":
                    python = os.path.basename(sys.executable)
                    e.add_note(
                        f"Try the asyncio REPL ({python} -m asyncio) to use"
                        f" top-level 'await' and run background asyncio tasks."
                    )
                self.showsyntaxerror(filename, source=source)
                return False
            except (OverflowError, ValueError):
                self.showsyntaxerror(filename, source=source)
                return False

            if code is None:
                return True

            result = self.runcode(code)
            if result is self.STATEMENT_FAILED:
                break
        return False