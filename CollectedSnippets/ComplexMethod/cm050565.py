def _prepare_collapsed_categories(self, categories_values, slide, next_category_to_open):
        """ Collapse the category if:
            - there is no category (the slides are uncategorized)
            - the category contains the current slide
            - the category is ongoing (has at least one slide completed but not all of its slides)
            - the category is the next one to be opened because the current one has just been completed
        """
        if request.env.user._is_public() or not slide.channel_id.is_member:
            return categories_values
        for category_dict in categories_values:
            category = category_dict.get('category')
            if not category or slide in category.slide_ids or category == next_category_to_open:
                category_dict['is_collapsed'] = True
            else:
                # collapse if category is ongoing
                slides_completion = category.slide_ids.mapped('user_has_completed')
                category_dict['is_collapsed'] = any(slides_completion) and not all(slides_completion)
        return categories_values