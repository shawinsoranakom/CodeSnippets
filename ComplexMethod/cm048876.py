def _get_card_element_values(self, record):
        """Helper to get the right value for dynamic fields."""
        self.ensure_one()
        result = {
            'image1': images[0] if (images := self.content_image1_path and self.content_image1_path in record and record.mapped(self.content_image1_path)) else False,
            'image2': images[0] if (images := self.content_image2_path and self.content_image2_path in record and record.mapped(self.content_image2_path)) else False,
        }
        campaign_text_element_fields = (
            ('header', 'content_header', 'content_header_dyn', 'content_header_path'),
            ('sub_header', 'content_sub_header', 'content_sub_header_dyn', 'content_sub_header_path'),
            ('section', 'content_section', 'content_section_dyn', 'content_section_path'),
            ('sub_section1', 'content_sub_section1', 'content_sub_section1_dyn', 'content_sub_section1_path'),
            ('sub_section2', 'content_sub_section2', 'content_sub_section2_dyn', 'content_sub_section2_path'),
        )
        for el, text_field, dyn_field, path_field in campaign_text_element_fields:
            if not self[dyn_field]:
                result[el] = self[text_field]
            elif not (field_path := self[path_field]):
                result[el] = record
            else:
                fnames = field_path.split('.')
                try:
                    value = record
                    while fnames and (fname := fnames.pop(0)):
                        value.fetch([fname])
                        value = value[fname]
                    m = record.mapped(field_path)
                    result[el] = m and m[0] or False
                except (AttributeError, ValueError):
                    # for generic image, or if field incorrect, return name of field
                    result[el] = field_path
                # force dates to their relevant timezone as that's what is usually wanted
                if (
                    isinstance(result[el], (date, datetime))
                    and (tz := record._mail_get_timezone())
                ):
                    result[el] = pytz.utc.localize(result[el]).astimezone(pytz.timezone(tz)).replace(tzinfo=None)
        return result