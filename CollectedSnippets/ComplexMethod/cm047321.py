def __init__(self, name, files, external_assets=(), env=None, css=True, js=True, debug_assets=False, rtl=False, assets_params=None, autoprefix=False):
        """
        :param name: bundle name
        :param files: files to be added to the bundle
        :param css: if css is True, the stylesheets files are added to the bundle
        :param js: if js is True, the javascript files are added to the bundle
        """
        self.name = name
        self.env = request.env if env is None else env
        self.javascripts = []
        self.templates = []
        self.stylesheets = []
        self.css_errors = []
        self.files = files
        self.rtl = rtl
        self.assets_params = assets_params or {}
        self.autoprefix = autoprefix
        self.has_css = css
        self.has_js = js
        self._checksum_cache = {}
        self.is_debug_assets = debug_assets
        self.external_assets = [
            url
            for url in external_assets
            if (css and url.rpartition('.')[2] in STYLE_EXTENSIONS) or (js and url.rpartition('.')[2] in SCRIPT_EXTENSIONS)
        ]

        # asset-wide html "media" attribute
        for f in files:
            extension = f['url'].rpartition('.')[2]
            params = {
                'url': f['url'],
                'filename': f['filename'],
                'inline': f['content'],
                'last_modified': None if self.is_debug_assets else f.get('last_modified'),
            }
            if css:
                css_params = {
                    'rtl': self.rtl,
                    'autoprefix': self.autoprefix,
                }
                if extension == 'sass':
                    self.stylesheets.append(SassStylesheetAsset(self, **params, **css_params))
                elif extension == 'scss':
                    self.stylesheets.append(ScssStylesheetAsset(self, **params, **css_params))
                elif extension == 'less':
                    self.stylesheets.append(LessStylesheetAsset(self, **params, **css_params))
                elif extension == 'css':
                    self.stylesheets.append(StylesheetAsset(self, **params, **css_params))
            if js:
                if extension == 'js':
                    self.javascripts.append(JavascriptAsset(self, **params))
                elif extension == 'xml':
                    self.templates.append(XMLAsset(self, **params))