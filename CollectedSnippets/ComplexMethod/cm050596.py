def _resequence_slides(self, slide, force_category=False):
        ids_to_resequence = self.slide_ids.ids
        index_of_added_slide = ids_to_resequence.index(slide.id)
        next_category_id = None
        if self.slide_category_ids:
            force_category_id = force_category.id if force_category else slide.category_id.id
            index_of_category = self.slide_category_ids.ids.index(force_category_id) if force_category_id else None
            if index_of_category is None:
                next_category_id = self.slide_category_ids.ids[0]
            elif index_of_category < len(self.slide_category_ids.ids) - 1:
                next_category_id = self.slide_category_ids.ids[index_of_category + 1]

        if next_category_id:
            added_slide_id = ids_to_resequence.pop(index_of_added_slide)
            index_of_next_category = ids_to_resequence.index(next_category_id)
            ids_to_resequence.insert(index_of_next_category, added_slide_id)
            for i, record in enumerate(self.env['slide.slide'].browse(ids_to_resequence)):
                record.write({'sequence': i + 1})  # start at 1 to make people scream
        else:
            slide.write({
                'sequence': self.env['slide.slide'].browse(ids_to_resequence[-1]).sequence + 1
            })