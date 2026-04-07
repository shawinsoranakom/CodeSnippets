def visit_desc_parameterlist(self, node):
        self.body.append("(")  # by default sphinx puts <big> around the "("
        self.optional_param_level = 0
        self.param_separator = node.child_text_separator
        # Counts 'parameter groups' being either a required parameter, or a set
        # of contiguous optional ones.
        required_params = [
            isinstance(c, addnodes.desc_parameter) for c in node.children
        ]
        # How many required parameters are left.
        self.required_params_left = sum(required_params)
        if sphinx_version < (7, 1):
            self.first_param = 1
        else:
            self.is_first_param = True
            self.params_left_at_level = 0
            self.param_group_index = 0
            self.list_is_required_param = required_params
            self.multi_line_parameter_list = False