def _load_records_create(self, data_list):
        with_import_values = [vals for vals in data_list if vals.get('import_attribute_values')]
        without_import_values = [vals for vals in data_list if not vals.get('import_attribute_values')]
        if not with_import_values:
            return super()._load_records_create(data_list)

        imported_product = super()._load_records_create(without_import_values)

        for vals in with_import_values:
            vals['name'] = (vals.get('name') or '').strip()
            if not vals['name'] and not vals.get('product_tmpl_id'):
                raise ValueError(self.env._('Unable to import products with attribute values but without name of product set'))

        contexted = self.sudo().with_context(
            create_product_product=False,
            update_product_template_attribute_values=True)
        PT = contexted.env['product.template']
        PP = contexted.env['product.product']
        PA = contexted.env['product.attribute']
        PAV = contexted.env['product.attribute.value']
        PTAL = contexted.env['product.template.attribute.line']

        ###############################################
        # Search product.attribute.value or create it #
        ###############################################

        # load/parse attribute value data
        attribute_to_values = defaultdict(OrderedSet)  # attribute_name => list[value_name]
        for vals in with_import_values:
            current_values = defaultdict(list)
            for value in vals['import_attribute_values'].split(','):
                attribute_name, value_name = value.split(':', 1) if ':' in value else (None, value)
                attribute_name = attribute_name and attribute_name.strip()
                value_name = value_name.strip()
                if not attribute_name:
                    raise ValueError(self.env._("Unable to import products with attribute value without attribute name (defined as: attribute:value): %s", vals['import_attribute_values']))
                if attribute_name in current_values:
                    raise ValueError(self.env._("It is not possible to import different values for the same attribute: %s", vals['import_attribute_values']))
                if value_name in current_values[attribute_name]:
                    raise ValueError(self.env._("Duplicate values in attribute values are not allowed: %s", vals['import_attribute_values']))
                attribute_to_values[attribute_name].add(value_name)
                current_values[attribute_name].append(value_name)

        # create missing attribute
        pa_records = {}  # attribute_name => Record<'product.attribute'>
        attribute_names = PA.search(Domain('name', 'in', list(attribute_to_values))).mapped('name')
        missing_pa = [
            {
                'name': attribute_name,
                'create_variant': 'dynamic',
                'display_type': 'radio',
            }
            for attribute_name in attribute_to_values
            if attribute_name not in attribute_names
        ]
        if missing_pa:
            for pa in PA.create(missing_pa):
                pa_records[pa.name] = pa

        # search attribute values
        pa_pav_records = {}  # (attribute_name, value_name) => Record<'product.attribute.value'>
        domain = Domain(False)
        for attribute_name, value_names in attribute_to_values.items():
            # search attribute values
            domain |= Domain('name', 'in', value_names) & Domain('attribute_id.name', '=', attribute_name)
        for pav in PAV.search(domain):
            pa_records[pav.attribute_id.name] = pav.attribute_id
            pa_pav_records[pav.attribute_id.name, pav.name] = pav

        # create missing attribute values
        missing_pav = [
            {
                'name': value_name,
                'attribute_id': pa_records[attribute_name].id,
            }
            for attribute_name, value_names in attribute_to_values.items()
            for value_name in value_names
            if (attribute_name, value_name) not in pa_pav_records
        ]
        if missing_pav:
            for pav in PAV.create(missing_pav):
                pa_pav_records[pav.attribute_id.name, pav.name] = pav

        ########################################
        # Search product.template or create it #
        ########################################

        product_templates = PT.search(
            Domain('name', 'in', [vals['name'] for vals in with_import_values]) |
            Domain('id', 'in', [vals.get('product_tmpl_id') for vals in with_import_values]))
        id2template = dict(zip(product_templates.ids, product_templates))  # id => Record<'product.template'>
        name2template = dict(zip(product_templates.mapped('name'), product_templates))  # template_name => Record<'product.template'>

        template_vals_list = {}
        for vals in with_import_values:
            name = vals['name']
            if name and name not in name2template and name not in template_vals_list:
                template_vals_list[name] = {key: value for key, value in vals.items() if PT._fields[key].required}

        # create the first product to have default values
        created_templates = PT.with_context(create_product_product=True).create(list(template_vals_list.values()))
        for rec in created_templates:
            id2template[rec.id] = rec
            name2template[rec.name] = rec

        field_names = list(with_import_values[0])
        default_values = {
            values['product_tmpl_id'][0]: values
            for values in (product_templates.product_variant_id + created_templates.product_variant_id).read(fields=['product_tmpl_id'] + field_names)
        }

        # Remove the useless product created with the product template.
        # It has no attribute value; it is not supposed to exist because we created some variants.
        useless_products = PP.search(Domain('product_tmpl_id', 'in', id2template.keys()) & Domain('product_template_attribute_value_ids', '=', False))
        useless_products._unlink_or_archive()

        ############################################################################
        # Create product.template.attribute.line if not exists or update value_ids #
        ############################################################################

        pt_to_attribute_to_values = defaultdict(list)  # (template_id, attribute_id) => list(Record<'product.attribute.value'>)
        for vals in with_import_values:
            for value in vals['import_attribute_values'].split(','):
                attribute_name, value_name = value.split(':', 1)
                pt = id2template.get(vals.get('product_tmpl_id')) or name2template.get(vals['name'])
                pav = pa_pav_records[attribute_name.strip(), value_name.strip()]
                pt_to_attribute_to_values[pt.id, pav.attribute_id.id].append(pav)
        domain = Domain(False)
        for template_id, attribute_id in pt_to_attribute_to_values:
            domain |= (Domain('product_tmpl_id', '=', template_id) &
                        Domain('attribute_id', '=', attribute_id))
        template_attribute_to_ptal = {  # (template_id, attribute_id) => ptal
            (ptal.product_tmpl_id.id, ptal.attribute_id.id): ptal
            for ptal in PTAL.search(domain)
        }
        ptals_to_create = []
        for (template_id, attribute_id), pavs in pt_to_attribute_to_values.items():
            ptal = template_attribute_to_ptal.get((template_id, attribute_id))
            if ptal:
                # add the new value ids
                ptal.value_ids = ptal.value_ids.union(*pavs)
            else:
                ptals_to_create.append({
                    'product_tmpl_id': template_id,
                    'attribute_id': attribute_id,
                    'value_ids': [value.id for value in pavs],
                })
        if ptals_to_create:
            ptals = PTAL.create(ptals_to_create)
            template_attribute_to_ptal.update(dict(zip(
                [(val['product_tmpl_id'], val['attribute_id']) for val in ptals_to_create],
                ptals
            )))

        ############################################
        # Get the product.template.attribute.value #
        ############################################

        template_value_to_ptav = {  # (template_id, value_id) => Record<'product.template.attribute.value'>
            (template_id, pav.id):
                template_attribute_to_ptal[template_id, attribute_id]
                    .product_template_value_ids.filtered(lambda v: v.product_attribute_value_id.id == pav.id)
            for (template_id, attribute_id), pavs in pt_to_attribute_to_values.items()
            for pav in pavs
        }

        ##################################################
        # Update data to import without constraint error #
        ##################################################

        for vals in with_import_values:
            name = vals.pop('name')
            if not vals.get('product_tmpl_id'):
                vals['product_tmpl_id'] = name2template[name].id

            vals['product_template_attribute_value_ids'] = [
                template_value_to_ptav[vals['product_tmpl_id'], pav.id].id
                for value in vals.pop('import_attribute_values').split(',')
                if ((p := value.split(':', 1)) and
                    (pav := pa_pav_records[p[0].strip(), p[1].strip()]))
            ]

        # If the imported cell/column is empty, use the default value (the first product value from the template)
        new_data_list = [
            {
                key: value if value else default_values[vals['product_tmpl_id']].get(key, False)
                for key, value in vals.items()
                if key not in ('import_attribute_values', 'id')
            }
            for vals in with_import_values
        ]
        products = super()._load_records_create(new_data_list)

        return imported_product.exists() + products