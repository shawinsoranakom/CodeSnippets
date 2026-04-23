def __init__(
        self,
        request,
        model,
        list_display,
        list_display_links,
        list_filter,
        date_hierarchy,
        search_fields,
        list_select_related,
        list_per_page,
        list_max_show_all,
        list_editable,
        model_admin,
        sortable_by,
        search_help_text,
    ):
        self.model = model
        self.opts = model._meta
        self.lookup_opts = self.opts
        self.root_queryset = model_admin.get_queryset(request)
        self.list_display = list_display
        self.list_display_links = list_display_links
        self.list_filter = list_filter
        self.has_filters = None
        self.has_active_filters = None
        self.clear_all_filters_qs = None
        self.date_hierarchy = date_hierarchy
        self.search_fields = search_fields
        self.list_select_related = list_select_related
        self.list_per_page = list_per_page
        self.list_max_show_all = list_max_show_all
        self.model_admin = model_admin
        self.preserved_filters = model_admin.get_preserved_filters(request)
        self.sortable_by = sortable_by
        self.search_help_text = search_help_text
        self.formset = None
        # Get search parameters from the query string.
        _search_form = self.search_form_class(request.GET)
        if not _search_form.is_valid():
            for error in _search_form.errors.values():
                messages.error(request, ", ".join(error))
        self.query = _search_form.cleaned_data.get(SEARCH_VAR) or ""
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 1))
        except ValueError:
            self.page_num = 1
        self.show_all = ALL_VAR in request.GET
        self.is_popup = IS_POPUP_VAR in request.GET
        self.add_facets = model_admin.show_facets is ShowFacets.ALWAYS or (
            model_admin.show_facets is ShowFacets.ALLOW and IS_FACETS_VAR in request.GET
        )
        self.is_facets_optional = model_admin.show_facets is ShowFacets.ALLOW
        to_field = request.GET.get(TO_FIELD_VAR)
        if to_field and not model_admin.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )
        self.to_field = to_field
        self.params = dict(request.GET.items())
        self.filter_params = dict(request.GET.lists())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
            del self.filter_params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]
            del self.filter_params[ERROR_FLAG]
        self.remove_facet_link = self.get_query_string(remove=[IS_FACETS_VAR])
        self.add_facet_link = self.get_query_string({IS_FACETS_VAR: True})

        if self.is_popup:
            self.list_editable = ()
        else:
            self.list_editable = list_editable
        self.queryset = self.get_queryset(request)
        self.get_results(request)
        if self.is_popup:
            title = gettext("Select %s")
        elif self.model_admin.has_change_permission(request):
            title = gettext("Select %s to change")
        else:
            title = gettext("Select %s to view")
        self.title = title % self.opts.verbose_name
        self.pk_attname = self.lookup_opts.pk.attname