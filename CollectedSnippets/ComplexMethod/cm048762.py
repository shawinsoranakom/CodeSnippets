def _check_children_scope(self):
        for tax in self:
            if tax._has_cycle('children_tax_ids'):
                raise ValidationError(_("Recursion found for tax “%s”.", tax.name))
            if any(
                child.type_tax_use not in ('none', tax.type_tax_use)
                or child.tax_scope not in (tax.tax_scope, False)
                for child in tax.children_tax_ids
            ):
                raise ValidationError(_('The application scope of taxes in a group must be either the same as the group or left empty.'))
            if any(
                child.amount_type == 'group'
                for child in tax.children_tax_ids
            ):
                raise ValidationError(_('Nested group of taxes are not allowed.'))