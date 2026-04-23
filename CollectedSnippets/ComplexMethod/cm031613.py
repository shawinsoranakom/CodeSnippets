def run(self) -> list[nodes.paragraph]:
        name = self.arguments[0]
        if len(self.arguments) >= 2 and self.arguments[1]:
            args = [
                arg
                for argument in self.arguments[1].strip("'\"").split(",")
                if (arg := argument.strip())
            ]
        else:
            args = []
        ids = []
        try:
            target = self.arguments[2].strip("\"'")
        except (IndexError, TypeError):
            target = None
        if not target:
            target = self.env.audit_events.id_for(name)
            ids.append(target)
        self.env.audit_events.add_event(name, args, (self.env.docname, target))

        node = nodes.paragraph("", classes=["audit-hook"], ids=ids)
        self.set_source_info(node)
        if self.content:
            node.rawsource = '\n'.join(self.content)  # for gettext
            self.state.nested_parse(self.content, self.content_offset, node)
        else:
            num_args = min(2, len(args))
            text = self._label[num_args].format(
                name=f"``{name}``",
                args=", ".join(f"``{a}``" for a in args),
            )
            node.rawsource = text  # for gettext
            parsed, messages = self.state.inline_text(text, self.lineno)
            node += parsed
            node += messages
        return [node]