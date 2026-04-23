def _parse_bundle_name(self, bundle_name, debug_assets):
        bundle_name, asset_type = bundle_name.rsplit('.', 1)
        rtl = False
        autoprefix = False
        if not debug_assets:
            bundle_name, min_ = bundle_name.rsplit('.', 1)
            if min_ != 'min':
                raise ValueError("'min' expected in extension in non debug mode")
        if asset_type == 'css':
            if bundle_name.endswith('.autoprefixed'):
                bundle_name = bundle_name[:-13]
                autoprefix = True
            if bundle_name.endswith('.rtl'):
                bundle_name = bundle_name[:-4]
                rtl = True
        elif asset_type != 'js':
            raise ValueError('Only js and css assets bundle are supported for now')
        if len(bundle_name.split('.')) != 2:
            raise ValueError(f'{bundle_name} is not a valid bundle name, should have two parts')
        return bundle_name, rtl, asset_type, autoprefix