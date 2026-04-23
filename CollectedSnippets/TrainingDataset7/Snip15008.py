def run(self):
        def args_to_win(cmdline):
            changed = False
            out = []
            for token in cmdline.split():
                if token[:2] == "./":
                    token = token[2:]
                    changed = True
                elif token[:2] == "~/":
                    token = "%HOMEPATH%\\" + token[2:]
                    changed = True
                elif token == "make":
                    token = "make.bat"
                    changed = True
                if "://" not in token and "git" not in cmdline:
                    out.append(token.replace("/", "\\"))
                    changed = True
                else:
                    out.append(token)
            if changed:
                return " ".join(out)
            return cmdline

        def cmdline_to_win(line):
            if line.startswith("# "):
                return "REM " + args_to_win(line[2:])
            if line.startswith("$ # "):
                return "REM " + args_to_win(line[4:])
            if line.startswith("$ ./manage.py"):
                return "manage.py " + args_to_win(line[13:])
            if line.startswith("$ manage.py"):
                return "manage.py " + args_to_win(line[11:])
            if line.startswith("$ ./runtests.py"):
                return "runtests.py " + args_to_win(line[15:])
            if line.startswith("$ ./"):
                return args_to_win(line[4:])
            if line.startswith("$ python3"):
                return "py " + args_to_win(line[9:])
            if line.startswith("$ python"):
                return "py " + args_to_win(line[8:])
            if line.startswith("$ "):
                return args_to_win(line[2:])
            return None

        def code_block_to_win(content):
            bchanged = False
            lines = []
            for line in content:
                modline = cmdline_to_win(line)
                if modline is None:
                    lines.append(line)
                else:
                    lines.append(self.WIN_PROMPT + modline)
                    bchanged = True
            if bchanged:
                return ViewList(lines)
            return None

        env = self.state.document.settings.env
        self.arguments = ["console"]
        lit_blk_obj = super().run()[0]

        # Only do work when the djangohtml HTML Sphinx builder is being used,
        # invoke the default behavior for the rest.
        if env.app.builder.name not in ("djangohtml", "json"):
            return [lit_blk_obj]

        lit_blk_obj["uid"] = str(env.new_serialno("console"))
        # Only add the tabbed UI if there is actually a Windows-specific
        # version of the CLI example.
        win_content = code_block_to_win(self.content)
        if win_content is None:
            lit_blk_obj["win_console_text"] = None
        else:
            self.content = win_content
            lit_blk_obj["win_console_text"] = super().run()[0].rawsource

        # Replace the literal_node object returned by Sphinx's CodeBlock with
        # the ConsoleNode wrapper.
        return [ConsoleNode(lit_blk_obj)]