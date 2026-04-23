def visit_node(node: Any) -> None:
            nonlocal last_pos
            if (
                node.kind == 'redirect'
                and hasattr(node, 'heredoc')
                and node.heredoc is not None
            ):
                # We're entering a heredoc - preserve everything as-is until we see EOF
                # Store the heredoc end marker (usually 'EOF' but could be different)
                between = command[last_pos : node.pos[0]]
                parts.append(between)
                # Add the heredoc start marker
                parts.append(command[node.pos[0] : node.heredoc.pos[0]])
                # Add the heredoc content as-is
                parts.append(command[node.heredoc.pos[0] : node.heredoc.pos[1]])
                last_pos = node.pos[1]
                return

            if node.kind == 'word':
                # Get the raw text between the last position and current word
                between = command[last_pos : node.pos[0]]
                word_text = command[node.pos[0] : node.pos[1]]

                # Add the between text, escaping special characters
                between = re.sub(r'\\([;&|><])', r'\\\\\1', between)
                parts.append(between)

                # Check if word_text is a quoted string or command substitution
                if (
                    (word_text.startswith('"') and word_text.endswith('"'))
                    or (word_text.startswith("'") and word_text.endswith("'"))
                    or (word_text.startswith('$(') and word_text.endswith(')'))
                    or (word_text.startswith('`') and word_text.endswith('`'))
                ):
                    # Preserve quoted strings, command substitutions, and heredoc content as-is
                    parts.append(word_text)
                else:
                    # Escape special chars in unquoted text
                    word_text = re.sub(r'\\([;&|><])', r'\\\\\1', word_text)
                    parts.append(word_text)

                last_pos = node.pos[1]
                return

            # Visit child nodes
            if hasattr(node, 'parts'):
                for part in node.parts:
                    visit_node(part)