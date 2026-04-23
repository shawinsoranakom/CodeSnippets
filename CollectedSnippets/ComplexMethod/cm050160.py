def _l10n_ar_identification_validation(self):
        for rec in self.filtered('vat'):
            try:
                module = rec._get_validation_module()
            except Exception as error:
                module = False
                _logger.runbot("Argentinean document was not validated: %s", repr(error))

            if not module:
                continue
            try:
                module.validate(rec.vat)
            except module.InvalidChecksum:
                raise ValidationError(_('The validation digit is not valid for "%s"',
                                        rec.l10n_latam_identification_type_id.name))
            except module.InvalidLength:
                raise ValidationError(_('Invalid length for "%s"', rec.l10n_latam_identification_type_id.name))
            except module.InvalidFormat:
                raise ValidationError(_('Only numbers allowed for "%s"', rec.l10n_latam_identification_type_id.name))
            except module.InvalidComponent:
                valid_cuit = ('20', '23', '24', '27', '30', '33', '34', '50', '51', '55')
                raise ValidationError(_('CUIT number must be prefixed with one of the following: %s', ', '.join(valid_cuit)))
            except Exception as error:
                raise ValidationError(repr(error))