def _get_icon_image(self):
        self.icon_image = ''
        for module in self:
            if not module.id:
                continue
            manifest = self.get_module_info(module.name)
            if module.icon:
                path = module.icon or ''
            elif manifest:
                path = manifest.get('icon', '')
            else:
                path = Manifest.for_addon('base').icon
            path = path.removeprefix("/")
            if path:
                try:
                    with tools.file_open(path, 'rb', filter_ext=('.png', '.svg', '.gif', '.jpeg', '.jpg')) as image_file:
                        module.icon_image = base64.b64encode(image_file.read())
                except OSError:
                    module.icon_image = ''
            countries = manifest.get('countries', [])
            country_code = len(countries) == 1 and countries[0]
            module.icon_flag = get_flag(country_code.upper()) if country_code else ''