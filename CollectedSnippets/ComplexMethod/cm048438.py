def action_put_in_pack(self, *, package_id=False, package_type_id=False, package_name=False):
        move_lines = self
        if self.env.context.get('all_move_line_ids'):
            move_lines = self.env['stock.move.line'].browse(self.env.context['all_move_line_ids'])
        # From the 'Moves' button, we want to take all move lines, without caring for picked or with/without packages.
        force_move_lines = bool(self.env.context.get('force_move_lines'))

        move_lines_to_pack, packages_to_pack = move_lines._get_lines_and_packages_to_pack(picked_first=not force_move_lines)
        done_pack = False
        if move_lines_to_pack:
            action = move_lines_to_pack._pre_put_in_pack_hook(move_lines, package_id, package_type_id, package_name, self.env.context.get('from_package_wizard'))
            if action:
                return action

            package = move_lines_to_pack._put_in_pack(package_id, package_type_id, package_name)
            done_pack = move_lines_to_pack._post_put_in_pack_hook(package)
        if done_pack and not force_move_lines:
            return done_pack
        elif packages_to_pack:
            if done_pack:
                packages_to_pack -= done_pack
                package_id = done_pack.id
            if packages_to_pack:
                return packages_to_pack.action_put_in_pack(package_id=package_id, package_type_id=package_type_id, package_name=package_name)