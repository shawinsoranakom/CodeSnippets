def _sync_plan_column(self, model):
        # Create/delete a new field/column on related models for this plan, and keep the name in sync.
        # Sort by parent_path to ensure parents are processed before children
        for plan in self.sorted('parent_path'):
            prev_stored = plan._find_plan_column(model)
            depth, name_related = plan._hierarchy_name()
            prev_related = plan._find_related_field(model)
            if plan.parent_id:
                # If there is a parent, we just need to make sure there is a field to group by the hierarchy level
                # of this plan, allowing to group by sub plan
                if prev_stored:
                    prev_stored.with_context({MODULE_UNINSTALL_FLAG: True}).unlink()
                description = f"{plan.root_id.name} ({depth})"
                if not prev_related:
                    self.env['ir.model.fields'].with_context(update_custom_fields=True).sudo().create({
                        'name': name_related,
                        'field_description': description,
                        'state': 'manual',
                        'model': model,
                        'model_id': self.env['ir.model']._get_id(model),
                        'ttype': 'many2one',
                        'relation': 'account.analytic.plan',
                        'related': plan._column_name() + '.plan_id' + '.parent_id' * (depth - 1),
                        'store': False,
                        'readonly': True,
                    })
                else:
                    prev_related.field_description = description
            else:
                # If there is no parent, then we need to create a new stored field as this is the root plan
                if prev_related:
                    prev_related.with_context({MODULE_UNINSTALL_FLAG: True}).unlink()
                description = plan.name
                if not prev_stored:
                    column = plan._strict_column_name()
                    field = self.env['ir.model.fields'].with_context(update_custom_fields=True).sudo().create({
                        'name': column,
                        'field_description': description,
                        'state': 'manual',
                        'model': model,
                        'model_id': self.env['ir.model']._get_id(model),
                        'ttype': 'many2one',
                        'relation': 'account.analytic.account',
                        'copied': True,
                        'on_delete': 'restrict',
                    })
                    Model = self.env[model]
                    if Model._auto:
                        tablename = Model._table
                        indexname = make_index_name(tablename, column)
                        create_index(self.env.cr, indexname, tablename, [column], 'btree', f'{column} IS NOT NULL')
                        field['index'] = True
                else:
                    prev_stored.field_description = description
        if self.children_ids:
            self.children_ids._sync_plan_column(model)