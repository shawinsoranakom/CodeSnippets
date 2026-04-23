def _load_records(self, data_list, update=False):
        """ Create or update records of this model, and assign XMLIDs.

            :param data_list: list of dicts with keys `xml_id` (XMLID to
                assign), `noupdate` (flag on XMLID), `values` (field values)
            :param update: should be ``True`` when upgrading a module

            :return: the records corresponding to ``data_list``
        """
        original_self = self.browse()

        imd = self.env['ir.model.data'].sudo()

        # The algorithm below partitions 'data_list' into three sets: the ones
        # to create, the ones to update, and the others. For each set, we assign
        # data['record'] for each data. All those records are then retrieved for
        # the result.

        # determine existing xml_ids
        xml_ids = [data['xml_id'] for data in data_list if data.get('xml_id')]
        existing = {
            ("%s.%s" % row[1:3]): row
            for row in imd._lookup_xmlids(xml_ids, self)
        }

        # determine which records to create and update
        to_create = []                  # list of data
        to_update = []                  # list of data
        imd_data_list = []              # list of data for _update_xmlids()

        for data in data_list:
            xml_id = data.get('xml_id')
            if not xml_id:
                vals = data['values']
                if vals.get('id'):
                    data['record'] = self.browse(vals['id'])
                    to_update.append(data)
                elif not update:
                    to_create.append(data)
                else:
                    raise ValidationError(_("Cannot update a record without specifying its id or xml_id"))
                continue
            row = existing.get(xml_id)
            if not row:
                to_create.append(data)
                continue
            d_id, d_module, d_name, d_model, d_res_id, d_noupdate, r_id = row
            if self._name != d_model:
                raise ValidationError(  # pylint: disable=missing-gettext
                    f"For external id {xml_id} "
                    f"when trying to create/update a record of model {self._name} "
                    f"found record of different model {d_model} ({d_id})"
                )
            record = self.browse(d_res_id)
            if r_id:
                data['record'] = record
                imd_data_list.append(data)
                if not (update and d_noupdate):
                    to_update.append(data)
            else:
                imd.browse(d_id).unlink()
                to_create.append(data)

        # update existing records
        for data in to_update:
            data['record']._load_records_write(data['values'])

        # check for records to create with an XMLID from another module
        module = self.env.context.get('install_module')
        if module:
            prefix = module + "."
            for data in to_create:
                if data.get('xml_id') and not data['xml_id'].startswith(prefix) and not self.env.context.get('foreign_record_to_create'):
                    _logger.warning("Creating record %s in module %s.", data['xml_id'], module)

        if self.env.context.get('import_file'):
            existing_modules = self.env['ir.module.module'].sudo().search([]).mapped('name')
            for data in to_create:
                xml_id = data.get('xml_id')
                if xml_id and not data.get('noupdate'):
                    module_name, sep, record_id = xml_id.partition('.')
                    if sep and module_name in existing_modules:
                        raise UserError(
                            _("The record %(xml_id)s has the module prefix %(module_name)s. This is the part before the '.' in the external id. Because the prefix refers to an existing module, the record would be deleted when the module is upgraded. Use either no prefix and no dot or a prefix that isn't an existing module. For example, __import__, resulting in the external id __import__.%(record_id)s.",
                              xml_id=xml_id, module_name=module_name, record_id=record_id))

        # create records
        if to_create:
            records = self._load_records_create([data['values'] for data in to_create])
            for data, record in zip(to_create, records):
                data['record'] = record
                if data.get('xml_id'):
                    # add XML ids for parent records that have just been created
                    for parent_model, parent_field in self._inherits.items():
                        if not data['values'].get(parent_field):
                            imd_data_list.append({
                                'xml_id': f"{data['xml_id']}_{parent_model.replace('.', '_')}",
                                'record': record[parent_field],
                                'noupdate': data.get('noupdate', False),
                            })
                    imd_data_list.append(data)

        # create or update XMLIDs
        imd._update_xmlids(imd_data_list, update)

        return original_self.concat(*(data['record'] for data in data_list))