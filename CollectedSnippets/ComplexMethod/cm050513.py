def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard in wizards:
            collaborator_ids_to_add = []
            collaborator_ids_to_add_with_limited_access = []
            collaborator_ids_vals_list = []
            project = wizard.resource_ref
            project_collaborator_ids_to_remove = [
                c.id
                for c in project.collaborator_ids
                if c.partner_id not in wizard.collaborator_ids.partner_id
            ]
            project_followers = project.message_partner_ids
            project_followers_to_add = []
            project_followers_to_remove = [
                partner.id
                for partner in project_followers
                if partner not in wizard.collaborator_ids.partner_id and partner.partner_share
            ]
            project_collaborator_per_partner_id = {c.partner_id.id: c for c in project.collaborator_ids}
            for collaborator in wizard.collaborator_ids:
                partner_id = collaborator.partner_id.id
                project_collaborator = project_collaborator_per_partner_id.get(partner_id, self.env['project.collaborator'])
                if collaborator.access_mode in ("edit", "edit_limited"):
                    limited_access = collaborator.access_mode == "edit_limited"
                    if not project_collaborator:
                        if limited_access:
                            collaborator_ids_to_add_with_limited_access.append(partner_id)
                        else:
                            collaborator_ids_to_add.append(partner_id)
                    elif project_collaborator.limited_access != limited_access:
                        collaborator_ids_vals_list.append(
                            Command.update(
                                project_collaborator.id,
                                {'limited_access': limited_access},
                            )
                        )
                elif project_collaborator:
                    project_collaborator_ids_to_remove.append(project_collaborator.id)
                if partner_id not in project_followers.ids:
                    project_followers_to_add.append(partner_id)
            if collaborator_ids_to_add:
                partners = project._get_new_collaborators(self.env['res.partner'].browse(collaborator_ids_to_add))
                collaborator_ids_vals_list.extend(Command.create({'partner_id': partner_id}) for partner_id in partners.ids)
                project.tasks.message_subscribe(partner_ids=partners.ids)
            if collaborator_ids_to_add_with_limited_access:
                partners = project._get_new_collaborators(self.env['res.partner'].browse(collaborator_ids_to_add_with_limited_access))
                collaborator_ids_vals_list.extend(
                    Command.create({'partner_id': partner_id, 'limited_access': True}) for partner_id in partners.ids
                )
            if project_collaborator_ids_to_remove:
                collaborator_ids_vals_list.extend(Command.delete(collaborator_id) for collaborator_id in project_collaborator_ids_to_remove)
            project_vals = {}
            if collaborator_ids_vals_list:
                project_vals['collaborator_ids'] = collaborator_ids_vals_list
            if project_vals:
                project.write(project_vals)
            if project_followers_to_add:
                project._add_followers(self.env['res.partner'].browse(project_followers_to_add))
            if project_followers_to_remove:
                project.message_unsubscribe(project_followers_to_remove)
        return wizards