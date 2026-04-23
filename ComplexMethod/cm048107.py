def _get_l10n_gr_edi_available_cls_type(self, inv_type: str, cls_category: str) -> str:
        """
        Helper for getting the l10n_gr_edi_available_cls_type string value.
        """
        available_cls_type = ''

        if (
                inv_type and
                cls_category and
                cls_category in CLASSIFICATION_MAP[inv_type]
        ):
            available_types = CLASSIFICATION_MAP[inv_type][cls_category]

            if available_types == 'all_above':
                available_types = set()
                for other_category in CLASSIFICATION_MAP[inv_type]:
                    same_category_type = other_category[:9] == cls_category[:9]  # category1* or category2*
                    contains_cls_types = isinstance(CLASSIFICATION_MAP[inv_type][other_category], tuple)
                    if same_category_type and contains_cls_types:
                        available_types.update(CLASSIFICATION_MAP[inv_type][other_category])
                available_types = tuple(available_types)

            if isinstance(available_types, tuple):
                available_cls_type = ','.join(available_types)

        return available_cls_type