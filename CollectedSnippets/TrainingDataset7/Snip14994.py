def visit_console_html(self, node):
    """Generate HTML for the console directive."""
    if self.builder.name in ("djangohtml", "json") and node["win_console_text"]:
        # Put a mark on the document object signaling the fact the directive
        # has been used on it.
        self.document._console_directive_used_flag = True
        uid = node["uid"]
        self.body.append("""\
<div class="console-block" id="console-block-%(id)s">
<input class="c-tab-unix" id="c-tab-%(id)s-unix" type="radio" name="console-%(id)s" \
checked>
<label for="c-tab-%(id)s-unix" title="Linux/macOS">&#xf17c/&#xf179</label>
<input class="c-tab-win" id="c-tab-%(id)s-win" type="radio" name="console-%(id)s">
<label for="c-tab-%(id)s-win" title="Windows">&#xf17a</label>
<section class="c-content-unix" id="c-content-%(id)s-unix">\n""" % {"id": uid})
        try:
            self.visit_literal_block(node)
        except nodes.SkipNode:
            pass
        self.body.append("</section>\n")

        self.body.append(
            '<section class="c-content-win" id="c-content-%(id)s-win">\n' % {"id": uid}
        )
        win_text = node["win_console_text"]
        highlight_args = {"force": True}
        linenos = node.get("linenos", False)

        def warner(msg):
            self.builder.warn(msg, (self.builder.current_docname, node.line))

        highlighted = self.highlighter.highlight_block(
            win_text, "doscon", warn=warner, linenos=linenos, **highlight_args
        )
        self.body.append(highlighted)
        self.body.append("</section>\n")
        self.body.append("</div>\n")
        raise nodes.SkipNode
    else:
        self.visit_literal_block(node)