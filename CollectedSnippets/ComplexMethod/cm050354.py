def _get_modules_from_apps(self, fields, module_type, module_name, domain=None, limit=None, offset=None):
        if 'name' not in fields:
            fields = fields + ['name']
        payload = {
            'params': {
                'series': major_version,
                'module_fields': fields,
                'module_type': module_type,
                'module_name': module_name,
                'domain': domain,
                'limit': limit,
                'offset': offset,
            }
        }
        import requests  # noqa: PLC0415
        try:
            resp = self._call_apps(json.dumps(payload))
            resp.raise_for_status()
            modules_list = resp.json().get('result', [])
            for mod in modules_list:
                module_name = mod['name']
                existing_mod = self.search([('name', '=', module_name), ('state', '=', 'installed')])
                mod['id'] = existing_mod.id if existing_mod else -1
                if 'icon' in fields:
                    mod['icon'] = f"{APPS_URL}{mod['icon']}"
                if 'state' in fields:
                    if existing_mod:
                        mod['state'] = 'installed'
                    else:
                        mod['state'] = 'uninstalled'
                if 'module_type' in fields:
                    mod['module_type'] = module_type
                if 'website' in fields:
                    mod['website'] = f"{APPS_URL}/apps/modules/{major_version}/{module_name}/"
            return modules_list
        except requests.exceptions.HTTPError:
            raise UserError(_('The list of industry applications cannot be fetched. Please try again later'))
        except requests.exceptions.ConnectionError:
            raise UserError(_('Connection to %s failed The list of industry modules cannot be fetched') % APPS_URL)