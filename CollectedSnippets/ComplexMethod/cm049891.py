def _get_source_from_ref(self, source_ref):
        """ From a source_reference, return either a mail template, either
        an ir ui view.

        :return: a 2-items tuple ``(template, view)`` where one is a recordset
          (may be void if ``source_ref`` is a void recordset, or a singleton)
          and the other one is ``False``. Always only one is set, as source is
          either a template, either a view.
        :rtype: tuple[BaseModel, Literal[False]] | tuple[Literal[False], BaseModel]
        """
        template, view = False, False
        if isinstance(source_ref, models.BaseModel):
            if source_ref._name == 'mail.template':
                template = source_ref
            elif source_ref._name == 'ir.ui.view':
                view = source_ref
            else:
                raise ValueError(
                    _('Invalid template or view source record %(svalue)s, is %(model)s instead',
                       svalue=source_ref,
                       model=source_ref._name,
                    ))
            if not template and not view:
                raise ValueError(
                    _('Mailing or posting with a source should not be called with an empty %(source_type)s',
                      source_type=_('template') if template is not False else _('view'))
                )
        elif isinstance(source_ref, str):
            try:
                res_model, res_id = self.env['ir.model.data']._xmlid_to_res_model_res_id(
                    source_ref,
                    raise_if_not_found=True
                )
            except ValueError as e:
                raise ValueError(
                    _('Invalid template or view source Xml ID %(source_ref)s does not exist anymore',
                      source_ref=source_ref)
                ) from e
            if res_model == 'mail.template':
                template = self.env['mail.template'].browse(res_id)
            elif res_model == 'ir.ui.view':
                view = self.env['ir.ui.view'].browse(res_id)
            else:
                raise ValueError(
                    _('Invalid template or view source reference %(svalue)s, is %(model)s instead',
                       svalue=source_ref,
                       model=res_model,
                    ))
        else:
            raise ValueError(
                _('Invalid template or view source %(svalue)s (type %(stype)s), should be a record or an XMLID',
                  svalue=source_ref,
                  stype=type(source_ref),
                ))
        return template, view