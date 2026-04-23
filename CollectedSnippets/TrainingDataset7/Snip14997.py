def run(self):
        if len(self.arguments) > 1:
            msg = """Only one argument accepted for directive '{directive_name}::'.
            Comments should be provided as content,
            not as an extra argument.""".format(directive_name=self.name)
            raise self.error(msg)

        env = self.state.document.settings.env
        ret = []
        node = addnodes.versionmodified()
        ret.append(node)

        if self.arguments[0] == env.config.django_next_version:
            node["version"] = "Development version"
        else:
            node["version"] = self.arguments[0]

        node["type"] = self.name
        if self.content:
            self.state.nested_parse(self.content, self.content_offset, node)
        try:
            env.get_domain("changeset").note_changeset(node)
        except ExtensionError:
            # Sphinx < 1.8: Domain 'changeset' is not registered
            env.note_versionchange(node["type"], node["version"], node, self.lineno)
        return ret