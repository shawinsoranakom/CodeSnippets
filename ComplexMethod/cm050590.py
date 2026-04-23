def _get_next_category(self):
        channel_category_ids = self.channel_id.slide_category_ids.ids
        if not channel_category_ids:
            return self.env['slide.slide']
        # If current slide is uncategorized and all the channel uncategorized slides are completed, return the first category
        if not self.category_id and all(self.channel_id.slide_ids.filtered(
            lambda s: not s.is_category and not s.category_id).mapped('user_has_completed')):
            return self.env['slide.slide'].browse(channel_category_ids[0])
        # If current category is completed and current category is not the last one, get next category
        elif self.user_has_completed_category and self.category_id.id in channel_category_ids and self.category_id.id != channel_category_ids[-1]:
            index_current_category = channel_category_ids.index(self.category_id.id)
            return self.env['slide.slide'].browse(channel_category_ids[index_current_category+1])
        return self.env['slide.slide']