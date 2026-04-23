def test_models_fields(self):
        """ check that all models and fields are reflected as expected. """
        model_names = [
            'decimal.precision.test',
            'domain.bool',
            'test_orm.any.child',
            'test_orm.any.parent',
            'test_orm.any.tag',
            'test_orm.attachment',
            'test_orm.attachment.host',
            'test_orm.autovacuumed',
            'test_orm.bar',
            'test_orm.binary_svg',
            'test_orm.cascade',
            'test_orm.category',
            'test_orm.city',
            'test_orm.company',
            'test_orm.company.attr',
            'test_orm.compute.container',
            'test_orm.compute.dynamic.depends',
            'test_orm.compute.inverse',
            'test_orm.compute.member',
            'test_orm.compute.onchange',
            'test_orm.compute.onchange.line',
            'test_orm.compute.readonly',
            'test_orm.compute.readwrite',
            'test_orm.compute.sudo',
            'test_orm.compute.unassigned',
            'test_orm.compute_editable',
            'test_orm.compute_editable.line',
            'test_orm.computed.modifier',
            'test_orm.country',
            'test_orm.course',
            'test_orm.create.performance',
            'test_orm.create.performance.line',
            'test_orm.creativework.book',
            'test_orm.creativework.edition',
            'test_orm.creativework.movie',
            'test_orm.crew',
            'test_orm.custom.table_query',
            'test_orm.custom.table_query_sql',
            'test_orm.custom.view',
            'test_orm.discussion',
            'test_orm.display',
            'test_orm.emailmessage',
            'test_orm.employer',
            'test_orm.empty_char',
            'test_orm.empty_int',
            'test_orm.field_with_caps',
            'test_orm.foo',
            'test_orm.group',
            'test_orm.hierarchy.head',
            'test_orm.hierarchy.node',
            'test_orm.indexed_translation',
            'test_orm.inverse_m2o_ref',
            'test_orm.lesson',
            'test_orm.message',
            'test_orm.mixed',
            'test_orm.mixin',
            'test_orm.model.all_access',
            'test_orm.model.no_access',
            'test_orm.model.some_access',
            'test_orm.model2.some_access',
            'test_orm.model3.some_access',
            'test_orm.model_a',
            'test_orm.model_active_field',
            'test_orm.model_b',
            'test_orm.model_binary',
            'test_orm.model_child',
            'test_orm.model_child_m2o',
            'test_orm.model_child_nocheck',
            'test_orm.model_constrained_unlinks',
            'test_orm.model_image',
            'test_orm.model_many2one_reference',
            'test_orm.model_parent',
            'test_orm.model_parent_m2o',
            'test_orm.model_selection_base',
            'test_orm.model_selection_non_stored',
            'test_orm.model_selection_related',
            'test_orm.model_selection_related_updatable',
            'test_orm.model_selection_required',
            'test_orm.model_selection_required_for_write_override',
            'test_orm.model_shared_cache_compute_line',
            'test_orm.model_shared_cache_compute_parent',
            'test_orm.modified',
            'test_orm.modified.line',
            'test_orm.monetary_base',
            'test_orm.monetary_custom',
            'test_orm.monetary_inherits',
            'test_orm.monetary_order',
            'test_orm.monetary_order_line',
            'test_orm.monetary_related',
            'test_orm.move',
            'test_orm.move_line',
            'test_orm.multi',
            'test_orm.multi.line',
            'test_orm.multi.line2',
            'test_orm.multi.tag',
            'test_orm.multi_compute_inverse',
            'test_orm.onchange.partial.view',
            'test_orm.one2many',
            'test_orm.one2many.line',
            'test_orm.order',
            'test_orm.order.line',
            'test_orm.partner',
            'test_orm.payment',
            'test_orm.person',
            'test_orm.person.account',
            'test_orm.pirate',
            'test_orm.precompute',
            'test_orm.precompute.combo',
            'test_orm.precompute.editable',
            'test_orm.precompute.line',
            'test_orm.precompute.monetary',
            'test_orm.precompute.readonly',
            'test_orm.precompute.required',
            'test_orm.prefetch',
            'test_orm.prefetch.line',
            'test_orm.prisoner',
            'test_orm.recursive',
            'test_orm.recursive.line',
            'test_orm.recursive.order',
            'test_orm.recursive.task',
            'test_orm.recursive.tree',
            'test_orm.related',
            'test_orm.related_bar',
            'test_orm.related_foo',
            'test_orm.related_inherits',
            'test_orm.related_translation_1',
            'test_orm.related_translation_2',
            'test_orm.related_translation_3',
            'test_orm.req_m2o',
            'test_orm.req_m2o_transient',
            'test_orm.selection',
            'test_orm.shared.compute',
            'test_orm.ship',
            'test_orm.state_mixin',
            'test_orm.team',
            'test_orm.team.member',
            'test_orm.transient_model',
            'test_orm.trigger.left',
            'test_orm.trigger.middle',
            'test_orm.trigger.right',
            'test_orm.unsearchable.o2m',
            'test_orm.user',
            'test_orm.view.str.id',
        ]
        ir_models = self.env['ir.model'].search([('model', 'in', model_names)])
        self.assertEqual(len(ir_models), len(model_names))
        for ir_model in ir_models:
            with self.subTest(model=ir_model.model):
                model = self.env[ir_model.model]
                self.assertModelXID(ir_model)
                self.assertEqual(ir_model.name, model._description or False)
                self.assertEqual(ir_model.state, 'manual' if model._custom else 'base')
                self.assertEqual(ir_model.transient, bool(model._transient))
                self.assertItemsEqual(ir_model.mapped('field_id.name'), list(model._fields))
                for ir_field in ir_model.field_id:
                    with self.subTest(field=ir_field.name):
                        field = model._fields[ir_field.name]
                        self.assertFieldXID(ir_field)
                        self.assertEqual(ir_field.model, field.model_name)
                        self.assertEqual(ir_field.field_description, field.string)
                        self.assertEqual(ir_field.help, field.help or False)
                        self.assertEqual(ir_field.ttype, field.type)
                        self.assertEqual(ir_field.state, 'manual' if field.manual else 'base')
                        self.assertEqual(ir_field.index, bool(field.index))
                        self.assertEqual(ir_field.store, bool(field.store))
                        self.assertEqual(ir_field.copied, bool(field.copy))
                        self.assertEqual(ir_field.related, field.related or False)
                        self.assertEqual(ir_field.readonly, bool(field.readonly))
                        self.assertEqual(ir_field.required, bool(field.required))
                        self.assertEqual(ir_field.selectable, bool(field.search or field.store))
                        self.assertEqual(FIELD_TRANSLATE.get(ir_field.translate or None, True), field.translate)
                        if field.relational:
                            self.assertEqual(ir_field.relation, field.comodel_name)
                        if field.type == 'one2many' and field.store:
                            self.assertEqual(ir_field.relation_field, field.inverse_name)
                        if field.type == 'many2many' and field.store:
                            self.assertEqual(ir_field.relation_table, field.relation)
                            self.assertEqual(ir_field.column1, field.column1)
                            self.assertEqual(ir_field.column2, field.column2)
                            relation = self.env['ir.model.relation'].search([('name', '=', field.relation)])
                            self.assertTrue(relation)
                            self.assertIn(relation.model.model, [field.model_name, field.comodel_name])
                        if field.type == 'selection':
                            selection = [(sel.value, sel.name) for sel in ir_field.selection_ids]
                            if isinstance(field.selection, list):
                                self.assertEqual(selection, field.selection)
                            else:
                                self.assertEqual(selection, [])
                            for sel in ir_field.selection_ids:
                                self.assertSelectionXID(sel)

                        field_description = field.get_description(self.env)
                        if field.type in ('many2many', 'one2many'):
                            self.assertFalse(field_description['sortable'])
                            self.assertIsInstance(field_description['domain'], (list, str))
                        elif field.store and field.column_type:
                            self.assertTrue(field_description['sortable'])