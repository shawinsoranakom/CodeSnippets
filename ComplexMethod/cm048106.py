def _get_l10n_gr_edi_available_cls_category(self, inv_type: str, category_type: str = '0') -> str:
        """
        Helper for getting the l10n_gr_edi_available_cls_category string value.
        :param str category_type: '0' (all, default) | '1' (income) | '2' (expense)
        """
        available_cls_category = ''

        if inv_type and CLASSIFICATION_MAP[inv_type] != 'associate':
            if category_type == '1':  # get only income categories
                available_cls_category = ','.join(category for category in CLASSIFICATION_MAP[inv_type]
                                                  if category[:9] == 'category1')
            elif category_type == '2':  # get only expense categories
                available_cls_category = ','.join(category for category in CLASSIFICATION_MAP[inv_type]
                                                  if category[:9] == 'category2')
            else:
                available_cls_category = ','.join(category for category in CLASSIFICATION_MAP[inv_type])

        return available_cls_category