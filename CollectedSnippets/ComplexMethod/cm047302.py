def _drop_column(self):
        from odoo.orm.model_classes import pop_field

        tables_to_drop = set()

        for field in self:
            if field.name in models.MAGIC_COLUMNS:
                continue
            model = self.env.get(field.model)
            is_model = model is not None
            if field.store:
                # TODO: Refactor this brol in master
                if is_model and sql.column_exists(self.env.cr, model._table, field.name) and \
                        sql.table_kind(self.env.cr, model._table) == sql.TableKind.Regular:
                    self.env.cr.execute(SQL('ALTER TABLE %s DROP COLUMN %s CASCADE',
                        SQL.identifier(model._table), SQL.identifier(field.name),
                    ))
                if field.state == 'manual' and field.ttype == 'many2many':
                    rel_name = field.relation_table or (is_model and model._fields[field.name].relation)
                    tables_to_drop.add(rel_name)
            if field.state == 'manual' and is_model:
                model_cls = self.env.registry[model._name]
                pop_field(model_cls, field.name)

        if tables_to_drop:
            # drop the relation tables that are not used by other fields
            self.env.cr.execute("""SELECT relation_table FROM ir_model_fields
                                WHERE relation_table IN %s AND id NOT IN %s""",
                             (tuple(tables_to_drop), tuple(self.ids)))
            tables_to_keep = {row[0] for row in self.env.cr.fetchall()}
            for rel_name in tables_to_drop - tables_to_keep:
                self.env.cr.execute(SQL('DROP TABLE %s', SQL.identifier(rel_name)))

        return True