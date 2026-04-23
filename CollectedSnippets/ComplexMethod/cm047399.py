def _validate_attributes(self, node, name_manager, node_info):
        """ Generic validation of node attributes. """

        # python expression used in for readonly, invisible, ...
        # and thus are only executed client side
        for attr in VIEW_MODIFIERS:
            py_expression = node.attrib.get(attr)
            if py_expression:
                self._validate_expression(node, name_manager, py_expression, f"modifier {attr!r}", node_info)

        for attr, expr in node.items():
            if attr in ('class', 't-att-class', 't-attf-class'):
                self._validate_classes(node, expr)

            elif attr == 'context':
                try:
                    vnames = get_expression_field_names(expr)
                except SyntaxError as e:
                    message = _('Invalid context: “%(expr)s” is not a valid Python expression \n\n %(error)s', expr=expr, error=e)
                    self._raise_view_error(message)
                if vnames:
                    name_manager.must_have_fields(node, vnames, node_info, f"context ({expr})")
                for key, val_ast in get_dict_asts(expr).items():
                    if key == 'group_by':  # only in context
                        if not isinstance(val_ast, ast.Constant) or not isinstance(val_ast.value, str):
                            msg = _(
                                '"group_by" value must be a string %(attribute)s=“%(value)s”',
                                attribute=attr, value=expr,
                            )
                            self._raise_view_error(msg, node)
                        group_by = val_ast.value
                        fname = group_by.split(':')[0]
                        if fname not in name_manager.model._fields:
                            msg = _(
                                'Unknown field “%(field)s” in "group_by" value in %(attribute)s=“%(value)s”',
                                field=fname, attribute=attr, value=expr,
                            )
                            self._raise_view_error(msg, node)

            elif attr in ('col', 'colspan'):
                # col check is mainly there for the tag 'group', but previous
                # check was generic in view form
                if not expr.isdigit():
                    self._raise_view_error(
                        _('“%(attribute)s” value must be an integer (%(value)s)',
                          attribute=attr, value=expr),
                        node,
                    )

            elif attr.startswith('decoration-'):
                vnames = get_expression_field_names(expr)
                if vnames:
                    name_manager.must_have_fields(node, vnames, node_info, f"{attr}={expr!r}")

            elif attr == 'data-bs-toggle' and expr == 'tab':
                if node.get('role') != 'tab':
                    msg = 'tab link (data-bs-toggle="tab") must have "tab" role'
                    self._log_view_warning(msg, node)
                aria_control = node.get('aria-controls') or node.get('t-att-aria-controls')
                if not aria_control and not node.get('t-attf-aria-controls'):
                    msg = 'tab link (data-bs-toggle="tab") must have "aria_control" defined'
                    self._log_view_warning(msg, node)
                if aria_control and '#' in aria_control:
                    msg = 'aria-controls in tablink cannot contains "#"'
                    self._log_view_warning(msg, node)

            elif attr == "role" and expr in ('presentation', 'none'):
                msg = ("A role cannot be `none` or `presentation`. "
                    "All your elements must be accessible with screen readers, describe it.")
                self._log_view_warning(msg, node)

            elif attr == 'group':
                msg = "attribute 'group' is not valid.  Did you mean 'groups'?"
                self._log_view_warning(msg, node)

            elif (re.match(r'^(t\-att\-|t\-attf\-)?data-tooltip(-template|-info)?$', attr)):
                self._raise_view_error(_("Forbidden attribute used in arch (%s).", attr), node)

            elif (attr.startswith("t-")):
                self._validate_qweb_directive(node, attr, node_info["view_type"])
                if (re.search(COMP_REGEX, expr)):
                    self._raise_view_error(_("Forbidden use of `__comp__` in arch."), node)