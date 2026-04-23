def _replace_placeholder(self, hook_key: str, result: str) -> str:
        """Replace all occurrences of a placeholder in the code with the hook result.

        During Jinja template rendering, hooks like ``def_kernel()``,
        ``load_input()``, and ``store_output()`` emit placeholder strings
        (e.g. ``<DEF_KERNEL>``, ``<LOAD_INPUT_A>``, ``<STORE_OUTPUT_0>``)
        into the rendered code and register corresponding hook functions in
        ``self.replacement_hooks``.  When ``finalize_hook()`` is called for
        each key, the hook function runs and this method replaces every
        occurrence of the placeholder with the result.

        Three replacement modes based on how each placeholder appears in
        the code:

        **Non-empty result, whole-line placeholder** — indent-propagating
        substitution.
            When the placeholder is the only non-whitespace content on a
            line, the entire line is replaced.  The placeholder line's
            leading whitespace (indent) is prepended to each result line
            that has no leading whitespace of its own; lines that are
            already indented are kept as-is.  This handles both hooks that
            return results at uniform indent 0 (e.g.
            ``ExternalTritonTemplateKernel``) and hooks that use the
            ``strip()`` convention (first line un-indented, subsequent
            lines pre-indented to the target level).

        **Non-empty result, inline placeholder** — direct substitution
        (``str.replace``).
            When the placeholder appears mid-line (e.g.
            ``{{gen_argdefs()}},``), all occurrences on that line are
            replaced with the result verbatim via ``str.replace``.

        **Empty result** — line removal.
            Every line whose only non-whitespace content is the placeholder
            is removed.  This handles cases like:

            - ``<DEF_KERNEL>`` returning ``""`` for
              ``ExternalTritonTemplateKernel`` (Helion), which emits its
              own kernel definition outside the template system.
            - ``<LOAD_INPUT_A>`` returning ``""`` when prologue fusion
              replaces the explicit load with inline computation from a
              fused producer.
            - ``<STORE_OUTPUT_0>`` returning ``""`` for
              ``ExternalTritonTemplateKernel`` outputs that have no
              matching epilogue consumer.
        """
        if hook_key not in self._code:
            return self._code

        # Empty result — remove every line that contains only the placeholder
        if not (result and result.strip()):
            lines = self._code.split("\n")
            return "\n".join(line for line in lines if line.strip() != hook_key)

        # Non-empty result — line-by-line replacement
        lines = self._code.split("\n")
        new_lines = []
        for line in lines:
            if line.strip() == hook_key:
                # Whole-line placeholder: decide how to indent the result.
                indent = line[: len(line) - len(line.lstrip())]
                result_lines = result.strip("\n").split("\n")
                non_empty = [rl for rl in result_lines if rl.strip()]
                all_unindented = bool(non_empty) and all(
                    not rl[0].isspace() for rl in non_empty
                )
                if all_unindented:
                    # Result is at uniform indent 0 (e.g.
                    # ExternalTritonTemplateKernel hooks) — apply the
                    # placeholder indent to every non-empty line.
                    indented = [
                        indent + rl if rl.strip() else rl for rl in result_lines
                    ]
                    new_lines.append("\n".join(indented).rstrip())
                else:
                    # Result has internal indentation (e.g. hooks using the
                    # strip() convention, or <DEF_KERNEL> with function
                    # bodies) — fall back to str.replace which prepends
                    # the placeholder line's whitespace to the first line
                    # only.
                    new_lines.append(line.replace(hook_key, result))
            elif hook_key in line:
                # Inline placeholder: simple substitution
                new_lines.append(line.replace(hook_key, result))
            else:
                new_lines.append(line)
        return "\n".join(new_lines)