def __str__(self):
        output = "<%s" % self.name
        for key, value in self.attributes:
            if value is not None:
                output += ' %s="%s"' % (key, value)
            else:
                output += " %s" % key
        if self.children:
            output += ">\n"
            output += "".join(
                [
                    html.escape(c) if isinstance(c, str) else str(c)
                    for c in self.children
                ]
            )
            output += "\n</%s>" % self.name
        else:
            output += ">"
        return output