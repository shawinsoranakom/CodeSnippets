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