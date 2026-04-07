def render(self, context):
        return SafeString("".join([node.render_annotated(context) for node in self]))