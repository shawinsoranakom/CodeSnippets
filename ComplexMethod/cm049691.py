def link_preview_metadata_internal(self, preview_url):
        try:
            Actions = request.env['ir.actions.actions']
            context = dict(request.env.context)
            parsed_preview_url = urlparse(preview_url)
            words = parsed_preview_url.path.strip('/').split('/')
            last_segment = words[-1]

            if not (
                last_segment.isnumeric()
                and (
                    parsed_preview_url.path.startswith("/odoo")
                    or parsed_preview_url.path.startswith("/web")
                    or parsed_preview_url.path.startswith("/@/")
                )
            ):
                # this could be a frontend or an external page
                link_preview_data = self.link_preview_metadata(preview_url)
                result = {}
                if link_preview_data and link_preview_data.get('og_description'):
                    result['description'] = link_preview_data['og_description']
                return result

            record_id = int(words.pop())
            action_name = words.pop()
            if (action_name.startswith('m-') or '.' in action_name) and action_name in request.env and not request.env[action_name]._abstract:
                # if path format is `odoo/<model>/<record_id>` so we use `action_name` as model name
                model_name = action_name.removeprefix('m-')
                model = request.env[model_name].with_context(context)
            else:
                action = Actions.sudo().search([('path', '=', action_name)])
                if not action:
                    return {'error_msg': _("Action %s not found, link preview is not available, please check your url is correct", action_name)}
                action_type = action.type
                if action_type != 'ir.actions.act_window':
                    return {'other_error_msg': _("Action %s is not a window action, link preview is not available", action_name)}
                action_sudo = request.env[action_type].sudo().browse(action.id)

                model = request.env[action_sudo.res_model].with_context(context)

            record = model.browse(record_id)

            result = {}
            if 'description' in record:
                result['description'] = html.fromstring(record.description).text_content() if record.description else ""

            if 'link_preview_name' in record:
                result['link_preview_name'] = record.link_preview_name
            elif 'display_name' in record:
                result['display_name'] = record.display_name

            return result
        except (MissingError) as e:
            return {'error_msg': _("Link preview is not available because %s, please check if your url is correct", str(e))}
        # catch all other exceptions and return the error message to display in the console but not blocking the flow
        except Exception as e:  # noqa: BLE001
            return {'other_error_msg': str(e)}