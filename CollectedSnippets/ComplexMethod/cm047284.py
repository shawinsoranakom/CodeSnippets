def _link_to_node(self, path, defer_load=False, lazy_load=False, media=None):
        ext = path.rsplit('.', maxsplit=1)[-1] if path else 'js'
        is_js = ext in SCRIPT_EXTENSIONS
        is_xml = ext in TEMPLATE_EXTENSIONS
        is_css = ext in STYLE_EXTENSIONS

        if is_js:
            is_asset_bundle = path and path.startswith('/web/assets/')
            attributes = {
                'type': 'text/javascript',
            }

            if defer_load:
                # Note that "lazy_load" will lead to "defer" being added in JS,
                # not here, otherwise this is not W3C valid (defer is probably
                # not even needed there anyways). See LAZY_LOAD_DEFER.
                attributes['defer'] = 'defer'
            if path:
                if lazy_load:
                    attributes['data-src'] = path
                else:
                    attributes['src'] = path

            if is_asset_bundle:
                attributes['onerror'] = "__odooAssetError=1"

            return ('script', attributes)

        if is_css:
            attributes = {
                'type': f'text/{ext}',  # we don't really expect to have anything else than pure css here
                'rel': 'stylesheet',
                'href': path,
                'media': media,
            }
            return ('link', attributes)

        if is_xml:
            attributes = {
                'type': 'text/xml',
                'async': 'async',
                'rel': 'prefetch',
                'data-src': path,
                }
            return ('script', attributes)

        return None