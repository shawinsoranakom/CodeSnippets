def _update_records(self, model_name, website):
        """
            This method:

            - Find and update existing records.

                For each model, overwrite the fields that are defined in the template (except few
                cases such as active) but keep inherited models to not lose customizations.

            - Create new records from templates for those that didn't exist.

            - Remove the models that existed before but are not in the template anymore.

                See _theme_cleanup for more information.


            There is a special 'while' loop around the 'for' to be able queue back models at the end
            of the iteration when they have unmet dependencies. Hopefully the dependency will be
            found after all models have been processed, but if it's not the case an error message will be shown.


            :param model_name: string with the technical name of the model to handle
                (the name must be one of the keys present in ``_theme_model_names``)
            :param website: ``website`` model for which the records have to be updated

            :raise MissingError: if there is a missing dependency.
        """
        self.ensure_one()

        remaining = self._get_module_data(model_name)
        last_len = -1
        while (len(remaining) != last_len):
            last_len = len(remaining)
            for rec in remaining:
                rec_data = rec._convert_to_base_model(website)
                if not rec_data:
                    _logger.info('Record queued: %s' % rec.display_name)
                    continue

                find = rec.with_context(active_test=False).mapped('copy_ids').filtered(lambda m: m.website_id == website)

                # special case for attachment
                # if module B override attachment from dependence A, we update it
                if not find and model_name == 'ir.attachment':
                    # In master, a unique constraint over (theme_template_id, website_id)
                    # will be introduced, thus ensuring unicity of 'find'
                    find = rec.copy_ids.search([('key', '=', rec.key), ('website_id', '=', website.id), ("original_id", "=", False)])

                if find:
                    imd = self.env['ir.model.data'].search([('model', '=', find._name), ('res_id', '=', find.id)])
                    if imd and imd.noupdate:
                        _logger.info('Noupdate set for %s (%s)' % (find, imd))
                    else:
                        # at update, ignore active field
                        if 'active' in rec_data:
                            rec_data.pop('active')
                        if model_name == 'ir.ui.view' and (find.arch_updated or find.arch == rec_data['arch']):
                            rec_data.pop('arch')
                        find.update(rec_data)
                        self._post_copy(rec, find)
                else:
                    new_rec = self.env[model_name].create(rec_data)
                    self._post_copy(rec, new_rec)

                remaining -= rec

        if len(remaining):
            error = 'Error - Remaining: %s' % remaining.mapped('display_name')
            _logger.error(error)
            raise MissingError(error)

        self._theme_cleanup(model_name, website)