def _parse_format_selection(tokens, inside_merge=False, inside_choice=False, inside_group=False):
            selectors = []
            current_selector = None
            for type_, string_, start, _, _ in tokens:
                # ENCODING is only defined in Python 3.x
                if type_ == getattr(tokenize, 'ENCODING', None):
                    continue
                elif type_ in [tokenize.NAME, tokenize.NUMBER]:
                    current_selector = FormatSelector(SINGLE, string_, [])
                elif type_ == tokenize.OP:
                    if string_ == ')':
                        if not inside_group:
                            # ')' will be handled by the parentheses group
                            tokens.restore_last_token()
                        break
                    elif inside_merge and string_ in ['/', ',']:
                        tokens.restore_last_token()
                        break
                    elif inside_choice and string_ == ',':
                        tokens.restore_last_token()
                        break
                    elif string_ == ',':
                        if not current_selector:
                            raise syntax_error('"," must follow a format selector', start)
                        selectors.append(current_selector)
                        current_selector = None
                    elif string_ == '/':
                        if not current_selector:
                            raise syntax_error('"/" must follow a format selector', start)
                        first_choice = current_selector
                        second_choice = _parse_format_selection(tokens, inside_choice=True)
                        current_selector = FormatSelector(PICKFIRST, (first_choice, second_choice), [])
                    elif string_ == '[':
                        if not current_selector:
                            current_selector = FormatSelector(SINGLE, 'best', [])
                        format_filter = _parse_filter(tokens)
                        current_selector.filters.append(format_filter)
                    elif string_ == '(':
                        if current_selector:
                            raise syntax_error('Unexpected "("', start)
                        group = _parse_format_selection(tokens, inside_group=True)
                        current_selector = FormatSelector(GROUP, group, [])
                    elif string_ == '+':
                        if not current_selector:
                            raise syntax_error('Unexpected "+"', start)
                        selector_1 = current_selector
                        selector_2 = _parse_format_selection(tokens, inside_merge=True)
                        if not selector_2:
                            raise syntax_error('Expected a selector', start)
                        current_selector = FormatSelector(MERGE, (selector_1, selector_2), [])
                    else:
                        raise syntax_error(f'Operator not recognized: "{string_}"', start)
                elif type_ == tokenize.ENDMARKER:
                    break
            if current_selector:
                selectors.append(current_selector)
            return selectors