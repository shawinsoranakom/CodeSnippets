def check(self, admin_obj, **kwargs):
        return [
            *super().check(admin_obj),
            *self._check_save_as(admin_obj),
            *self._check_save_on_top(admin_obj),
            *self._check_inlines(admin_obj),
            *self._check_list_display(admin_obj),
            *self._check_list_display_links(admin_obj),
            *self._check_list_filter(admin_obj),
            *self._check_list_select_related(admin_obj),
            *self._check_list_per_page(admin_obj),
            *self._check_list_max_show_all(admin_obj),
            *self._check_list_editable(admin_obj),
            *self._check_search_fields(admin_obj),
            *self._check_date_hierarchy(admin_obj),
            *self._check_actions(admin_obj),
        ]