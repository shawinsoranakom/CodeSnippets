def write(self, vals):

        self._strip_formula(vals)

        tax_tags_expressions = self.filtered(lambda x: x.engine == 'tax_tags')

        if vals.get('engine') == 'tax_tags':
            # We already generate the tags for the expressions receiving a new engine
            tags_create_vals = []
            for expression_with_new_engine in self - tax_tags_expressions:
                tag_name = vals.get('formula') or expression_with_new_engine.formula
                country = expression_with_new_engine.report_line_id.report_id.country_id
                if not self.env['account.account.tag']._get_tax_tags(tag_name, country.id):
                    tags_create_vals += self.env['account.report.expression']._get_tags_create_vals(
                        tag_name,
                        country.id,
                    )

            self.env['account.account.tag'].create(tags_create_vals)

        # In case the engine is changed we don't propagate any change to the tags themselves
        if 'formula' not in vals or (vals.get('engine') and vals['engine'] != 'tax_tags'):
            return super().write(vals)

        former_formulas_by_country = defaultdict(lambda: [])
        for expr in tax_tags_expressions:
            former_formulas_by_country[expr.report_line_id.report_id.country_id].append(expr.formula)

        result = super().write(vals)
        for country, former_formulas_list in former_formulas_by_country.items():
            for former_formula in former_formulas_list:
                new_tax_tags = self.env['account.account.tag']._get_tax_tags(vals['formula'], country.id)

                if not new_tax_tags:
                    # If new tags already exist, nothing to do ; else, we must create them or update existing tags.
                    former_tax_tags = self.env['account.account.tag']._get_tax_tags(former_formula, country.id)

                    if former_tax_tags and all(tag_expr in self for tag_expr in former_tax_tags._get_related_tax_report_expressions()):
                        # If we're changing the formula of all the expressions using that tag, rename the tag
                        former_tax_tags._update_field_translations('name', {'en_US': vals['formula']})
                    else:
                        # Else, create a new tag. Its the compute functions will make sure it is properly linked to the expressions
                        tag_vals = self.env['account.report.expression']._get_tags_create_vals(vals['formula'], country.id)
                        self.env['account.account.tag'].create(tag_vals)

        return result