def do(self) -> None:
        r: CompletingReader
        r = self.reader  # type: ignore[assignment]
        last_is_completer = r.last_command_is(self.__class__)
        if r.cmpltn_action:
            if last_is_completer:  # double-tab: execute action
                msg = r.cmpltn_action[1]()
                r.cmpltn_action = None  # consumed
                if msg:
                    r.msg = msg
                    r.cmpltn_message_visible = True
                    r.invalidate_message()
            else:  # other input since last tab: cancel action
                r.cmpltn_action = None

        immutable_completions = r.assume_immutable_completions
        completions_unchangable = last_is_completer and immutable_completions
        stem = r.get_stem()
        if not completions_unchangable:
            r.cmpltn_menu_choices, r.cmpltn_action = r.get_completions(stem)

        completions = r.cmpltn_menu_choices
        if not completions:
            if not r.cmpltn_action:
                r.error("no matches")
        elif len(completions) == 1:
            completion = stripcolor(completions[0])
            if completions_unchangable and len(completion) == len(stem):
                r.msg = "[ sole completion ]"
                r.cmpltn_message_visible = True
                r.invalidate_message()
            r.insert(completion[len(stem):])
        else:
            clean_completions = [stripcolor(word) for word in completions]
            p = prefix(clean_completions, len(stem))
            if p:
                r.insert(p)
            if last_is_completer:
                r.cmpltn_menu_visible = True
                r.cmpltn_menu, r.cmpltn_menu_end = build_menu(
                    r.console, completions, r.cmpltn_menu_end,
                    r.use_brackets, r.sort_in_column)
                if r.msg:
                    r.msg = ""
                    r.cmpltn_message_visible = False
                    r.invalidate_message()
                r.invalidate_overlay()
            elif not r.cmpltn_menu_visible:
                if stem + p in clean_completions:
                    r.msg = "[ complete but not unique ]"
                    r.cmpltn_message_visible = True
                    r.invalidate_message()
                else:
                    r.msg = "[ not unique ]"
                    r.cmpltn_message_visible = True
                    r.invalidate_message()

        if r.cmpltn_action:
            if r.msg and r.cmpltn_message_visible:
                # There is already a message (eg. [ not unique ]) that
                # would conflict for next tab: cancel action
                r.cmpltn_action = None
            else:
                r.msg = r.cmpltn_action[0]
                r.cmpltn_message_visible = True
                r.invalidate_message()