def _validate_parent_menu(self):
        """
        Ensure valid menu hierarchy and mega menu constraints.

        Rules enforced:
        - Menus must not exceed two levels of nesting.
        - A mega menu must not have a parent or child.
        - Menus with children cannot be added as a submenu under another menu.
        """
        for record in self:
            parent_menu = record.parent_id.sudo() if record.parent_id else None

            # Check hierarchy level
            level = 0
            current_menu = parent_menu
            while current_menu:
                level += 1
                current_menu = current_menu.parent_id
                if level > 2:
                    raise UserError(_("Menus cannot have more than two levels of hierarchy."))

            if parent_menu:
                # Mega menu constraint
                if parent_menu.is_mega_menu or (record.is_mega_menu and (parent_menu.parent_id or record.child_id)):
                    raise UserError(_("A mega menu cannot have a parent or child menu."))

                # Submenu structure constraint
                if record.child_id and (parent_menu.parent_id or record.child_id.child_id):
                    raise UserError(_("Menus with child menus cannot be added as a submenu."))