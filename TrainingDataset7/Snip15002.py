def visit_versionmodified(self, node):
        self.body.append(self.starttag(node, "div", CLASS=node["type"]))
        version_text = self.version_text.get(node["type"])
        if version_text:
            title = "%s%s" % (version_text % node["version"], ":" if len(node) else ".")
            self.body.append('<span class="title">%s</span> ' % title)