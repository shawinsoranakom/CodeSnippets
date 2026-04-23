def test_04_url_cook_lang_not_available(self):
        """ `nearest_lang` should filter out lang not available in frontend.
        Eg: 1. go in backend in english -> request.env.context['lang'] = `en_US`
            2. go in frontend, the request.env.context['lang'] is passed through
               `nearest_lang` which should not return english. More then a
               misbehavior it will crash in website language selector template.
        """
        # 1. Load backend
        self.authenticate('admin', 'admin')
        r = self.url_open('/odoo')
        self.assertEqual(r.status_code, 200)

        for line in r.text.splitlines():
            _, match, session_info_str = line.partition('odoo.__session_info__ = ')
            if match:
                session_info = json.loads(session_info_str[:-1])
                self.assertEqual(session_info['user_context']['lang'], 'en_US', "ensure english was loaded")
                self.assertEqual(session_info['bundle_params']['lang'], 'en_US', "ensure bundle use english")
                break
        else:
            raise ValueError('Session info not found in web page')

        # 2. Remove en_US from frontend
        self.website.language_ids = self.lang_fr
        self.website.default_lang_id = self.lang_fr

        # 3. Ensure visiting /contactus do not crash
        url = '/contactus'
        r = self.url_open(url)
        self.assertEqual(r.status_code, 200)

        if 'lang="fr-FR"' not in r.text:
            doc = lxml.html.document_fromstring(r.text)
            self.assertEqual(doc.get('lang'), 'fr-FR', "Ensure contactus did not soft crash + loaded in correct lang")

        for line in r.text.splitlines():
            _, match, session_info_str = line.partition('odoo.__session_info__ = ')
            if match:
                session_info = json.loads(session_info_str[:-1])
                self.assertEqual(session_info['bundle_params']['lang'], 'fr_FR', "ensure bundle use french")
                break
        else:
            raise ValueError('Session info not found in web page')