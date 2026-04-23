def write(self, vals):
        '''COW for ir.ui.view. This way editing websites does not impact other
        websites. Also this way newly created websites will only
        contain the default views.
        '''
        current_website_id = self.env.context.get('website_id')
        if not current_website_id or self.env.context.get('no_cow'):
            return super().write(vals)

        # We need to consider inactive views when handling multi-website cow
        # feature (to copy inactive children views, to search for specific
        # views, ...)
        # Website-specific views need to be updated first because they might
        # be relocated to new ids by the cow if they are involved in the
        # inheritance tree.
        for view in self.with_context(active_test=False).sorted('website_id.id'):
            # Make sure views which are written in a website context receive
            # a value for their 'key' field
            if not view.key and not vals.get('key'):
                view.with_context(no_cow=True).key = 'website.key_%s' % str(uuid.uuid4())[:6]

            pages = view.page_ids

            # No need of COW if the view is already specific
            if view.website_id:
                super(IrUiView, view).write(vals)
                continue

            # Ensure the cache of the pages stay consistent when doing COW.
            # This is necessary when writing view fields from a page record
            # because the generic page will put the given values on its cache
            # but in reality the values were only meant to go on the specific
            # page. Invalidate all fields and not only those in vals because
            # other fields could have been changed implicitly too.
            pages.flush_recordset()
            pages.invalidate_recordset()

            # If already a specific view for this generic view, write on it
            website_specific_view = view.search([
                ('key', '=', view.key),
                ('website_id', '=', current_website_id)
            ], limit=1)
            if website_specific_view:
                super(IrUiView, website_specific_view).write(vals)
                continue

            # Set key to avoid copy() to generate an unique key as we want the
            # specific view to have the same key
            copy_vals = {'website_id': current_website_id, 'key': view.key}
            # Copy with the 'inherit_id' field value that will be written to
            # ensure the copied view's validation works
            if vals.get('inherit_id'):
                copy_vals['inherit_id'] = vals['inherit_id']
            website_specific_view = view.copy(copy_vals)

            view._create_website_specific_pages_for_view(website_specific_view,
                                                         view.env['website'].browse(current_website_id))

            for inherit_child in view.inherit_children_ids.filter_duplicate().sorted(key=lambda v: (v.priority, v.id)):
                if inherit_child.website_id.id == current_website_id:
                    # In the case the child was already specific to the current
                    # website, we cannot just reattach it to the new specific
                    # parent: we have to copy it there and remove it from the
                    # original tree. Indeed, the order of children 'id' fields
                    # must remain the same so that the inheritance is applied
                    # in the same order in the copied tree.
                    child = inherit_child.copy({'inherit_id': website_specific_view.id, 'key': inherit_child.key})
                    inherit_child.inherit_children_ids.write({'inherit_id': child.id})
                    inherit_child.unlink()
                else:
                    # Trigger COW on inheriting views
                    inherit_child.write({'inherit_id': website_specific_view.id})

            super(IrUiView, website_specific_view).write(vals)

        return True