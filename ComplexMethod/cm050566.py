def slides_channel(self, slide_category=None, slug_tags=None, my=0, page=1, **post):
        my = 1 if str(my) == '1' else 0  # if in the URL parameters, it will be a string instead of a number
        if slug_tags and slug_tags.count(',') > 0 and request.httprequest.method == 'GET' and not post.get('prevent_redirect'):
            # Previously, the tags were searched using GET, which caused issues with crawlers (too many hits)
            # We replaced those with POST to avoid that, but it's not sufficient as bots "remember" crawled pages for a while
            # This permanent redirect is placed to instruct the bots that this page is no longer valid
            # TODO: remove in a few stable versions (v19?), including the "prevent_redirect" param in templates
            # Note: We allow a single tag to be GET, to keep crawlers & indexes on those pages
            # What we really want to avoid is combinatorial explosions
            return request.redirect('/slides', code=301)

        render_values = self.slides_channel_values(
            slide_category=slide_category, slug_tags=slug_tags, my=my, page=page, **post)
        if page > 1 and not render_values['channels']:
            # Refining search may reduce results; if no results and not on page 1, reset to page 1.
            if slug_tags:
                return request.redirect(f"/slides/tag/{slug_tags}?{keep_query('*')}")
            return request.redirect(f"/slides?{keep_query('*')}")
        return request.render('website_slides.courses_home', render_values)