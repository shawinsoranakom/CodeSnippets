def preprocess_css(self, debug=False, old_attachments=None):
        """
            Checks if the bundle contains any sass/less content, then compiles it to css.
            If user language direction is Right to Left then consider css files to call run_rtlcss,
            css files are also stored in ir.attachment after processing done by rtlcss.
            Returns the bundle's flat css.
        """
        if self.stylesheets:
            compiled = ""
            for atype in (SassStylesheetAsset, ScssStylesheetAsset, LessStylesheetAsset):
                assets = [asset for asset in self.stylesheets if isinstance(asset, atype)]
                if assets:
                    source = '\n'.join([asset.get_source() for asset in assets])
                    compiled += self.compile_css(assets[0].compile, source)

            if self.autoprefix:
                compiled = self.autoprefix_css(compiled)

            # We want to run rtlcss on normal css, so merge it in compiled
            if self.rtl:
                stylesheet_assets = [asset for asset in self.stylesheets if not isinstance(asset, (SassStylesheetAsset, ScssStylesheetAsset, LessStylesheetAsset))]
                compiled += '\n'.join([asset.get_source() for asset in stylesheet_assets])
                compiled = self.run_rtlcss(compiled)

            if not self.css_errors and old_attachments:
                self._unlink_attachments(old_attachments)
                old_attachments = None

            fragments = self.rx_css_split.split(compiled)
            at_rules = fragments.pop(0)
            if at_rules:
                # Sass and less moves @at-rules to the top in order to stay css 2.1 compatible
                self.stylesheets.insert(0, StylesheetAsset(self, inline=at_rules))
            while fragments:
                asset_id = fragments.pop(0)
                asset = next(asset for asset in self.stylesheets if asset.id == asset_id)
                asset._content = fragments.pop(0)

        return '\n'.join(asset.minify() for asset in self.stylesheets)