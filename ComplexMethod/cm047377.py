def _compute_invalid_locators(self):
        def assess_locator(source, spec):
            node = None
            with suppress(ValidationError):  # Syntax error
                # If locate_node returns None here:
                # Invalid expression: Ok Syntax, but cannot be anchored to the parent view.
                node = self.locate_node(source, spec)

            if node is None:
                return {
                    "tag": spec.tag,
                    "attrib": dict(spec.attrib),
                    "sourceline": spec.sourceline,
                }
            return None

        self.invalid_locators = []
        for view in self:
            if not view.inherit_id or not view.arch:
                continue
            try:
                # When an arch above the current one is invalid, we don't want to raise
                # instead, we want to continue using the form view.
                # This can happen when an invalid xpath has been forcibly written without checking
                # Via SQL or during the upgrade process
                source = view.with_context(ir_ui_view_tree_cut_off_view=view)._get_combined_arch()
            except (ValidationError, ValueError):  # Xpath syntax Invalid , Xpath element unfound
                # Flagging The field as not empty and with custom information.
                # We don't do anything with the object, but the information
                # may give some clues for debugging.
                # Also, for display purposes in Form view, the field needs not be falsy.
                view.invalid_locators = [{"broken_hierarchy": True}]
                continue

            invalid_locators = []
            specs = collections.deque([etree.fromstring(view.arch)])
            while specs:
                spec = specs.popleft()
                if isinstance(spec, etree._Comment):
                    continue
                if spec.tag == 'data':
                    specs.extend(spec)
                    continue

                if invalid_locator := assess_locator(source, spec):
                    invalid_locators.append(invalid_locator)
                else:
                    position, mode = spec.get("position"), spec.get("mode")
                    for sub_spec in spec:
                        sub_position = sub_spec.get("position")
                        if sub_position == "move" and (position != "replace" or mode != "inner"):
                            if invalid_move := assess_locator(source, sub_spec):
                                invalid_locators.append(invalid_move)
                        elif sub_position:
                            invalid_locators.append({
                                "tag": sub_spec.tag,
                                "attrib": dict(sub_spec.attrib),
                                "sourceline": sub_spec.sourceline,
                            })

                    try:
                        # Since subsequent xpaths may be dependent on previous xpaths, we apply the spec.
                        source = apply_inheritance_specs(source, spec)
                    except ValueError as e:
                        # This function is only interested in locating invalid locators.
                        # Here, ValueError is raised for:
                        #   Invalid mode attribute
                        #   Invalid attributes attribute
                        #   Invalid position
                        #   Element <attribute> with 'add' or 'remove' cannot contain text
                        #   Invalid separator for python expressions in attributes
                        pass
            view.invalid_locators = invalid_locators