def _add_validation_flag(self, combined_arch, view=None, arch=None):
        """ Add a validation flag on elements in ``combined_arch`` or ``arch``.
        This is part of the partial validation of views.

        :param Element combined_arch: the architecture to be modified by ``arch``
        :param view: an optional view inheriting ``self``
        :param Element arch: an optional modifying architecture from inheriting
            view ``view``
        """
        # validate_view_ids is either falsy (no validation), True (full
        # validation) or a collection of ids (partial validation)
        validate_view_ids = self.env.context.get('validate_view_ids')
        if not validate_view_ids:
            return

        if validate_view_ids is True or self.id in validate_view_ids:
            # optimization, flag the root node
            combined_arch.set('__validate__', '1')
            return

        if view is None or view.id not in validate_view_ids:
            return

        for node in arch.xpath('//*[@position]'):
            if node.get('position') in ('after', 'before', 'inside'):
                # validate the elements being inserted, except the ones that
                # specify a move, as in:
                #   <field name="foo" position="after">
                #       <field name="bar" position="move"/>
                #   </field>
                for child in node.iterchildren(tag=etree.Element):
                    if not child.get('position'):
                        child.set('__validate__', '1')
            if node.get('position') == 'replace':
                # validate everything, since this impacts the whole arch
                combined_arch.set('__validate__', '1')
                break
            if node.get('position') == 'attributes':
                # validate the element being modified by adding
                # attribute "__validate__" on it:
                #   <field name="foo" position="attributes">
                #       <attribute name="readonly">1</attribute>
                #       <attribute name="__validate__">1</attribute>    <!-- add this -->
                #   </field>
                node.append(E.attribute('1', name='__validate__'))