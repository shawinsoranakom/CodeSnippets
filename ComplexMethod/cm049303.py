def _build_vcard(self):
        """ Build the partner's vCard.
            :returns a vobject.vCard object
        """
        if not vobject:
            return False
        vcard = vobject.vCard()
        # Name
        n = vcard.add('n')
        n.value = vobject.vcard.Name(family=self.name or self.complete_name or '')
        # Formatted Name
        fn = vcard.add('fn')
        fn.value = self.name or self.complete_name or ''
        # Address
        adr = vcard.add('adr')
        adr.value = vobject.vcard.Address(street=self.street or '', city=self.city or '', code=self.zip or '')
        if self.state_id:
            adr.value.region = self.state_id.name
        if self.country_id:
            adr.value.country = self.country_id.name
        # Email
        if self.email:
            email = vcard.add('email')
            email.value = self.email
            email.type_param = 'INTERNET'
        # Telephone numbers
        if self.phone:
            tel = vcard.add('tel')
            tel.type_param = 'work'
            tel.value = self.phone
        # URL
        if self.website:
            url = vcard.add('url')
            url.value = self.website
        # Organisation
        if self.commercial_company_name:
            org = vcard.add('org')
            org.value = [self.commercial_company_name]
        if self.function:
            function = vcard.add('title')
            function.value = self.function
        # Photo
        photo = vcard.add('photo')
        photo.value = b64decode(self.avatar_512)
        photo.encoding_param = 'B'
        photo.type_param = 'JPG'
        return VComponentProxy(vcard)