def _error_message_group_inconsistency(self, name, missing_groups, reasons):
        does_not_exist = name not in self.model._fields and name not in self.available_names
        if not (does_not_exist or missing_groups is False):
            return None, None

        elements = [
            f'<field name="{node.get("name")}"/>' if node.tag == 'field' else f'<{node.tag}>'
            for _item_groups, _use, node in reasons
        ]

        debug = []
        if does_not_exist:
            debug.append(_(
                "- field “%(name)s” does not exist in model “%(model)s”.",
                name=name,
                model=self.model._name,
            ))
        else:
            field_groups = self._get_field_groups(name)
            debug.append(_(
                "- field “%(name)s” is accessible for groups: %(field_groups)s",
                name=name,
                field_groups=_('Only super user has access') if field_groups.is_empty() else field_groups,
            ))

        for item_groups, _use, node in reasons:
            clone = etree.Element(node.tag, node.attrib)
            clone.attrib.pop('__validate__', None)
            clone.attrib.pop('__groups_key__', None)
            debug.append(_(
                "- element “%(node)s” is shown in the view for groups: %(groups)s",
                node=etree.tostring(clone, encoding='unicode'),
                groups=(
                    _('Free access') if item_groups.is_universal() else
                    _('Accessible only for the super user') if item_groups.is_empty() else
                    item_groups
                ),
            ))

        message = Markup(
            "<b>{header}</b><br/>{body}<br/>{footer}<br/>{debug}"
        ).format(
            header=_("Access Rights Inconsistency"),
            body=_(
                "This view may not work for all users: some users may have a "
                "combination of groups where the elements %(elements)s are displayed, "
                "but they depend on the field %(field)s that is not accessible. "
                "You might fix this by modifying user groups to make sure that all users "
                "who have access to those elements also have access to the field, "
                "typically via group implications. Alternatively, you could "
                "adjust the “%(groups)s” or “%(invisible)s” attributes for these fields, "
                "to make sure they are always available together.",
                elements=Markup(", ").join(
                    Markup("<b><tt>%s</tt></b>") % element for element in elements
                ),
                field=Markup("<b><tt>%s</tt></b>") % name,
                groups=Markup("<i>groups</i>"),
                invisible=Markup("<i>invisible</i>"),
            ),
            footer=_("Debugging information:"),
            debug=Markup("<br/>").join(debug),
        )

        return message, 'does_not_exist' if does_not_exist else 'inconsistency'