def write(self, vals):
        result = True
        # archiving a blog post, unpublished the blog post
        if 'active' in vals and not vals['active']:
            vals['is_published'] = False
        for post in self:
            copy_vals = dict(vals)
            published_in_vals = set(vals.keys()) & {'is_published', 'website_published'}
            if (published_in_vals and 'published_date' not in vals and
                    (not post.published_date or post.published_date <= fields.Datetime.now())):
                copy_vals['published_date'] = vals[list(published_in_vals)[0]] and fields.Datetime.now() or False
            result &= super(BlogPost, post).write(copy_vals)
        self._check_for_publication(vals)
        return result