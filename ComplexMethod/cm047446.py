def ignore(o2m_field, m2o_field):
            if not comodel._auto or comodel._abstract:
                return True  # tableless
            if comodel.is_transient():
                return True  # transient models shouldn't have a lot of records
            if not (m2o_field.store and m2o_field.column_type):
                return True  # the m2o isn't stored in database
            if o2m_field.comodel_name in BTREE_INDEX_IGNORE_MODELS:
                return True  # the o2m field's model is in the model ignore list
            if str(m2o_field) in BTREE_INDEX_IGNORE_FIELDS:
                return True  # the m2o field is in the field ignore list
            if m2o_field.index in BTREE_INDEX_PY_DEFS:
                return True  # the field is already indexed in the definition
            ir_model_id = self.env['ir.model']._get_id(comodel._name)
            modules = self.env['ir.model.data'].search_fetch([
                ('model', '=', 'ir.model'), ('res_id', '=', ir_model_id)
            ], ['module']).mapped('module')
            # ruff: noqa: SIM103
            if modules and all('test' in module for module in modules):
                return True  # skip model if it's in a test module
            return False