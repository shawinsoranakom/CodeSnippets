def extend_nodelist(self, nodelist, node, token):
        # Check that non-text nodes don't appear before an extends tag.
        if node.must_be_first and nodelist.contains_nontext:
            if self.origin.template_name:
                origin = repr(self.origin.template_name)
            else:
                origin = "the template"
            raise self.error(
                token,
                "{%% %s %%} must be the first tag in %s." % (token.contents, origin),
            )
        if not isinstance(node, TextNode):
            nodelist.contains_nontext = True
        # Set origin and token here since we can't modify the node __init__()
        # method.
        node.token = token
        node.origin = self.origin
        nodelist.append(node)