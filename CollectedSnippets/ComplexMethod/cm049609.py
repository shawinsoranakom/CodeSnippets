def _disable_unused_snippets_assets(self):
        snippet_assets = self.env['ir.asset'].with_context(active_test=False).search_fetch(
            [('path', 'like', '/static%/snippets/')],
            ['active', 'path'], order='id')
        snippet_re = re.compile(r'(\w*)\/.*\/snippets\/(\w*)\/(\d{3})(?:_\w*)?\.(js|scss)')
        # regex will match /module/static/[.../]/snippets/snippet_id/XXX[_variable].asset_type
        # _variable is not kept since only module, snippet_id, asset_version (XXX), asset_type are relevant
        html_fields = self._get_html_fields()
        snippet_used = {}
        for snippet_asset in snippet_assets:
            match = snippet_re.match(snippet_asset.path)
            if not match:
                continue
            (snippet_module, snippet_id, asset_version, asset_type) = match.groups()
            if asset_type == 'scss':
                asset_type = 'css'
            key = (snippet_id, asset_version, asset_type)  # module is not relevant, we want the first one in the asset id order to filter module extension
            if key not in snippet_used:
                snippet_used[key] = self._is_snippet_used(snippet_module, snippet_id, asset_version, asset_type, html_fields)
            is_snippet_used = snippet_used[key]
            if is_snippet_used != snippet_asset.active:
                snippet_asset.active = is_snippet_used
                # Handle missing data-snippet attributes
                if snippet_id == 's_quotes_carousel' and asset_type == 'css' and asset_version in ['000', '001']:
                    old_blockquote_key = ('s_blockquote', '000', 'css')
                    if not snippet_used.get(old_blockquote_key):
                        snippet_used[old_blockquote_key] = True
                        old_blockquote_asset = snippet_assets.filtered(lambda asset: asset.path == 'website/static/src/snippets/s_blockquote/000.scss')
                        if old_blockquote_asset and not old_blockquote_asset.active:
                            old_blockquote_asset.active = True
        self.env['ir.asset'].flush_model()