def set_profiling(self, profile=None, collectors=None, params=None):
        """
        Enable or disable profiling for the current user.

        :param profile: ``True`` to enable profiling, ``False`` to disable it.
        :param list collectors: optional list of collectors to use (string)
        :param dict params: optional parameters set on the profiler object
        """
        # Note: parameters are coming from a rpc calls or route param (public user),
        # meaning that corresponding session variables are client-defined.
        # This allows to activate any profiler, but can be
        # dangerous handling request.session.profile_collectors/profile_params.
        if profile:
            limit = self._enabled_until()
            _logger.info("User %s started profiling", self.env.user.name)
            if not limit:
                request.session['profile_session'] = None
                if self.env.user._is_system():
                    return {
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'base.enable.profiling.wizard',
                            'target': 'new',
                            'views': [[False, 'form']],
                        }
                raise UserError(self.env._('Profiling is not enabled on this database. Please contact an administrator.'))
            if not request.session.get('profile_session'):
                request.session['profile_session'] = make_session(self.env.user.name)
                request.session['profile_expiration'] = limit
                if request.session.get('profile_collectors') is None:
                    request.session['profile_collectors'] = []
                if request.session.get('profile_params') is None:
                    request.session['profile_params'] = {}
        elif profile is not None:
            request.session['profile_session'] = None

        if collectors is not None:
            request.session['profile_collectors'] = collectors

        if params is not None:
            request.session['profile_params'] = params

        return {
            'session': request.session.get('profile_session'),
            'collectors': request.session.get('profile_collectors'),
            'params': request.session.get('profile_params'),
        }