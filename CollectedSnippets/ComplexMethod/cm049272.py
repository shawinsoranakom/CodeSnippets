def generate_bundles(self, unlink=True):
        if unlink:
            self.env['ir.attachment'].search([('url', '=like', '/web/assets/%')]).unlink()  # delete existing attachement
        installed_module_names = self.env['ir.module.module'].search([('state', '=', 'installed')]).mapped('name')
        bundles = {
            key
            for module in installed_module_names
            for key in get_manifest(module).get('assets', [])
        }

        for bundle_name in bundles:
            with mute_logger('odoo.addons.base.models.assetsbundle'):
                for assets_type in 'css', 'js':
                    try:
                        start_t = time.time()
                        css = assets_type == 'css'
                        js = assets_type == 'js'
                        bundle = self.env['ir.qweb']._get_asset_bundle(bundle_name, css=css, js=js)
                        if assets_type == 'css' and bundle.stylesheets:
                            bundle.css()
                        if assets_type == 'js' and bundle.javascripts:
                            bundle.js()
                        yield (f'{bundle_name}.{assets_type}', time.time() - start_t)
                    except ValueError:
                        _logger.info('Error detected while generating bundle %r %s', bundle_name, assets_type)