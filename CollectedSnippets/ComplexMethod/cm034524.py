def do_var_prompt(
        self,
        varname: str,
        private: bool = True,
        prompt: str | None = None,
        encrypt: str | None = None,
        confirm: bool = False,
        salt_size: int | None = None,
        salt: str | None = None,
        default: str | None = None,
        unsafe: bool = False,
    ) -> str:
        result = None
        if sys.__stdin__.isatty():

            do_prompt = self.prompt

            if prompt and default is not None:
                msg = "%s [%s]: " % (prompt, default)
            elif prompt:
                msg = "%s: " % prompt
            else:
                msg = 'input for %s: ' % varname

            if confirm:
                while True:
                    result = do_prompt(msg, private)
                    second = do_prompt("confirm " + msg, private)
                    if result == second:
                        break
                    self.display("***** VALUES ENTERED DO NOT MATCH ****")
            else:
                result = do_prompt(msg, private)
        else:
            result = None
            self.warning("Not prompting as we are not in interactive mode")

        # if result is false and default is not None
        if not result and default is not None:
            result = default

        if encrypt:
            # Circular import because encrypt needs a display class
            from ansible.utils.encrypt import do_encrypt
            result = do_encrypt(result, encrypt, salt_size=salt_size, salt=salt)

        # handle utf-8 chars
        result = to_text(result, errors='surrogate_or_strict')

        if not unsafe:
            # to maintain backward compatibility, assume these values are safe to template
            result = TrustedAsTemplate().tag(result)

        return result