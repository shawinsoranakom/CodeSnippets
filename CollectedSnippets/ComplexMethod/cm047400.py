def _validate_classes(self, node, expr):
        """ Validate the classes present on node. """
        classes = set(expr.split(' '))
        # Be careful: not always true if it is an expression
        # example: <div t-attf-class="{{!selection_mode ? 'oe_kanban_color_' + kanban_getcolor(record.color.raw_value) : ''}} oe_kanban_card oe_kanban_global_click oe_applicant_kanban oe_semantic_html_override">
        if 'modal' in classes and node.get('role') != 'dialog':
            msg = '"modal" class should only be used with "dialog" role'
            self._log_view_warning(msg, node)

        if 'modal-header' in classes and node.tag != 'header':
            msg = '"modal-header" class should only be used in "header" tag'
            self._log_view_warning(msg, node)

        if 'modal-body' in classes and node.tag != 'main':
            msg = '"modal-body" class should only be used in "main" tag'
            self._log_view_warning(msg, node)

        if 'modal-footer' in classes and node.tag != 'footer':
            msg = '"modal-footer" class should only be used in "footer" tag'
            self._log_view_warning(msg, node)

        if 'tab-pane' in classes and node.get('role') != 'tabpanel':
            msg = '"tab-pane" class should only be used with "tabpanel" role'
            self._log_view_warning(msg, node)

        if 'nav-tabs' in classes and node.get('role') != 'tablist':
            msg = 'A tab list with class nav-tabs must have role="tablist"'
            self._log_view_warning(msg, node)

        if any(klass.startswith('alert-') for klass in classes):
            if (
                node.get('role') not in ('alert', 'alertdialog', 'status')
                and 'alert-link' not in classes
            ):
                msg = ("An alert (class alert-*) must have an alert, alertdialog or "
                        "status role or an alert-link class. Please use alert and "
                        "alertdialog only for what expects to stop any activity to "
                        "be read immediately.")
                self._log_view_warning(msg, node)

        if any(klass.startswith('fa-') for klass in classes):
            description = 'A <%s> with fa class (%s)' % (node.tag, expr)
            self._validate_fa_class_accessibility(node, description)

        if any(klass.startswith('btn') for klass in classes):
            if node.tag in ('a', 'button', 'select'):
                pass
            elif node.tag == 'input' and node.get('type') in ('button', 'submit', 'reset'):
                pass
            elif any(klass in classes for klass in ('btn-group', 'btn-toolbar', 'btn-addr')):
                pass
            elif node.tag == 'field' and node.get('widget') == 'url':
                pass
            else:
                msg = ("A simili button must be in tag a/button/select or tag `input` "
                        "with type button/submit/reset or have class in "
                        "btn-group/btn-toolbar/btn-addr")
                self._log_view_warning(msg, node)