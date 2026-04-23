def _compute_display_name(self):
        type_description = dict(self._fields['type']._description_selection(self.env))
        for partner in self:
            if partner.env.context.get("formatted_display_name"):
                name = partner.name or ''
                if partner.parent_id or partner.company_name:
                    name = (f"{partner.company_name or partner.parent_id.name} \t "
                            f"--{partner.name or type_description.get(partner.type, '')}--")

                if partner.env.context.get('show_email') and partner.email:
                    name = f"{name} \t --{partner.email}--"
                elif partner.env.context.get('partner_show_db_id'):
                    name = f"{name} \t --{partner.id}--"

            else:
                name = partner.with_context(lang=self.env.lang)._get_complete_name()
                if partner.env.context.get('partner_show_db_id'):
                    name = f"{name} ({partner.id})"
                if partner.env.context.get('show_email') and partner.email:
                    name = f"{name} <{partner.email}>"
                if partner.env.context.get('show_address'):
                    name = name + "\n" + partner._display_address(without_company=True)

                if partner.env.context.get('show_vat') and partner.vat:
                    if partner.env.context.get('show_address'):
                        name = f"{name} \n {partner.vat}"
                    else:
                        name = f"{name} - {partner.vat}"

            # Remove extra empty lines
            name = re.sub(r'\s+\n', '\n', name)
            partner.display_name = name.strip()