def get_assets_editor_resources(self, key, get_views=True, get_scss=True, get_js=True, bundles=False, bundles_restriction=[], only_user_custom_files=True):
        """
        Transmit the resources the assets editor needs to work.

        Params:
            key (str): the key of the view the resources are related to

            get_views (bool, default=True):
                True if the views must be fetched

            get_scss (bool, default=True):
                True if the style must be fetched

            get_js (bool, default=True):
                True if the javascript must be fetched

            bundles (bool, default=False):
                True if the bundles views must be fetched

            bundles_restriction (list, default=[]):
                Names of the bundles in which to look for scss files
                (if empty, search in all of them)

            only_user_custom_files (bool, default=True):
                True if only user custom files must be fetched

        Returns:
            dict: views, scss, js
        """
        # Related views must be fetched if the user wants the views and/or the style
        views = request.env["ir.ui.view"].with_context(no_primary_children=True, __views_get_original_hierarchy=[], is_customization_code=False).get_related_views(key, bundles=bundles)
        views = views.read(['name', 'id', 'key', 'xml_id', 'arch', 'active', 'inherit_id'])

        scss_files_data_by_bundle = []
        js_files_data_by_bundle = []

        if get_scss:
            scss_files_data_by_bundle = self._load_resources('scss', views, bundles_restriction, only_user_custom_files)
        if get_js:
            js_files_data_by_bundle = self._load_resources('js', views, bundles_restriction, only_user_custom_files)

        return {
            'views': get_views and views or [],
            'scss': get_scss and scss_files_data_by_bundle or [],
            'js': get_js and js_files_data_by_bundle or [],
        }