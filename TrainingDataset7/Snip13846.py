def __init__(self, test_case, template_name, msg_prefix="", count=None):
        self.test_case = test_case
        self.template_name = template_name
        self.msg_prefix = msg_prefix
        self.count = count

        self.rendered_templates = []
        self.context = ContextList()