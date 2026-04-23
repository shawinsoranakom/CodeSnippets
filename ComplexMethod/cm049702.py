def save(self, value, xpath=None):
        """ Update a view section. The view section may embed fields to write

        Note that `self` record might not exist when saving an embed field

        :param str xpath: valid xpath to the tag to replace
        """
        self.ensure_one()

        arch_section = html.fromstring(
            value, parser=html.HTMLParser(encoding='utf-8'))

        if xpath is None:
            # value is an embedded field on its own, not a view section
            self.save_embedded_field(arch_section)
            return

        for el in self.extract_embedded_fields(arch_section):
            self.save_embedded_field(el)

            # transform embedded field back to t-field
            el.getparent().replace(el, self.to_field_ref(el))

        for el in self.extract_oe_structures(arch_section):
            if self.save_oe_structure(el):
                # empty oe_structure in parent view
                empty = self.to_empty_oe_structure(el)
                if el == arch_section:
                    arch_section = empty
                else:
                    el.getparent().replace(el, empty)

        # TODO: in master, remove this.
        # This bit of code patches a view. Patching of this view is necessary
        # for some xpath in the following views if the view
        # `website.footer_copyright_company_name` has been COW after:
        #   - `website.template_footer_mega`
        #   - `website.template_footer_mega_columns`
        #   - `website.template_footer_mega_links`
        # The patch consists of adding the class `col-md` to the divs with
        # `col-sm` in the footer of the view `web.frontend_layout`, which is
        # the grand-parent of `website.layout`
        if self.key in {
            'website.footer_copyright_company_name',
            'website.template_footer_mega',
            'website.template_footer_mega_columns',
            'website.template_footer_mega_links',
        }:
            ancestor = self.inherit_id.inherit_id.inherit_id
            arch = etree.fromstring(ancestor.arch.encode('utf-8'))
            has_change = False
            for node in arch.xpath("//div[hasclass('o_footer_copyright')]//div[hasclass('col-sm')]"):
                if 'col-md' not in node.get('class'):
                    node.set('class', node.get('class') + ' col-md')
                    has_change = True
            if has_change:
                ancestor.with_context(no_cow=True, delayed_translations=False).write({'arch': etree.tostring(arch, encoding='unicode')})

        new_arch = self.replace_arch_section(xpath, arch_section)
        old_arch = etree.fromstring(self.arch.encode('utf-8'))
        if not self._are_archs_equal(old_arch, new_arch):
            self._set_noupdate()
            self.write({'arch': etree.tostring(new_arch, encoding='unicode')})
            self._copy_custom_snippet_translations(self, 'arch_db')