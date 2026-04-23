def _get_formatted_value(self):
            # self must be named so to be considered in the translation logic
            field_ = records._fields[field_name]
            field_type_ = field_.type
            for record_ in records:
                value_ = record_[field_name]
                if field_type_ == 'boolean':
                    formatted_value_ = _("Yes") if value_ else _("No")
                elif field_type_ == 'monetary':
                    currency_id_ = record_[field_.get_currency_field(record_)]
                    formatted_value_ = format_amount(
                        self.env, value_, currency_id_ or order.currency_id
                    )
                elif not value_ and field_type_ not in {'integer', 'float'}:
                    formatted_value_ = ''
                elif field_type_ == 'date':
                    formatted_value_ = format_date(self.env, value_)
                elif field_type_ == 'datetime':
                    formatted_value_ = format_datetime(self.env, value_, tz=tz, dt_format=False)
                elif field_type_ == 'selection' and value_:
                    formatted_value_ = dict(field_._description_selection(self.env))[value_]
                elif field_type_ in {'one2many', 'many2one', 'many2many'}:
                    formatted_value_ = ', '.join([v.display_name for v in value_])
                else:
                    formatted_value_ = str(value_)

                yield formatted_value_