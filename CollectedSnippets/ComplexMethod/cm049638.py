def filter_duplicate(self):
        """ Filter current recordset only keeping the most suitable view per distinct key.
            Every non-accessible view will be removed from the set:

              * In non website context, every view with a website will be removed
              * In a website context, every view from another website
        """
        current_website_id = self.env.context.get('website_id')
        if not current_website_id:
            return self.filtered(lambda view: not view.website_id)

        specific_views_keys = {view.key for view in self if view.website_id.id == current_website_id and view.key}
        most_specific_views = []
        for view in self:
            # specific view: add it if it's for the current website and ignore
            # it if it's for another website
            if view.website_id and view.website_id.id == current_website_id:
                most_specific_views.append(view)
            # generic view: add it only if, for the current website, there is no
            # specific view for this view (based on the same `key` attribute)
            elif not view.website_id and view.key not in specific_views_keys:
                most_specific_views.append(view)

        return self.browse().union(*most_specific_views)