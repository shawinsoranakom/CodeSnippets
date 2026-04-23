def _handle_visibility(self, do_raise=True):
        """ Check the visibility set on the main view and raise 403 if you should not have access.
            Order is: Public, Connected, Has group, Password

            It only check the visibility on the main content, others views called stay available in rpc.
        """
        error = False

        self = self.sudo()

        visibility = self._get_cached_visibility()

        if visibility and not request.env.user.has_group('website.group_website_designer'):
            if (visibility == 'connected' and request.website.is_public_user()):
                error = werkzeug.exceptions.Forbidden()
            elif visibility == 'password' and \
                    (request.website.is_public_user() or self.id not in request.session.get('views_unlock', [])):
                pwd = request.params.get('visibility_password')
                if pwd and self.env.user._crypt_context().verify(
                        pwd, self.visibility_password):
                    request.session.setdefault('views_unlock', list()).append(self.id)
                else:
                    error = werkzeug.exceptions.Forbidden('website_visibility_password_required')

            if visibility not in ('password', 'connected'):
                try:
                    self._check_view_access()
                except AccessError:
                    error = werkzeug.exceptions.Forbidden()

        if error:
            if do_raise:
                raise error
            else:
                return False
        return True