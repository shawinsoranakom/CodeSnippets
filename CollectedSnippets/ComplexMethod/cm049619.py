def filter_duplicate(self, website_id=None):
        """ Filter current recordset only keeping the most suitable asset per distinct name.
            Every non-accessible asset will be removed from the set:

              * In non website context, every asset with a website will be removed
              * In a website context, every asset from another website
        """
        if website_id is None:
            website_id = self.env['website'].get_current_website(fallback=False).id
        if not website_id:
            return self.filtered(lambda asset: not asset.website_id)

        specific_asset_keys = {asset.key for asset in self if asset.website_id.id == website_id and asset.key}
        most_specific_assets = []
        for asset in self:
            if asset.website_id:
                # specific asset: add it if it's for the current website and ignore
                # it if it's for another website
                if asset.website_id.id == website_id:
                    most_specific_assets.append(asset)
                continue
            elif not asset.key:
                # no key: added either way
                most_specific_assets.append(asset)
            elif asset.key not in specific_asset_keys:
                # generic asset: add it iff for the current website, there is no
                # specific asset for this asset (based on the same `key` attribute)
                most_specific_assets.append(asset)

        return self.browse().union(*most_specific_assets)