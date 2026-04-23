def _serve_db(self):
        """ Load the ORM and use it to process the request. """
        # reuse the same cursor for building, checking the registry, for
        # matching the controller endpoint and serving the data
        cr = None
        try:
            # get the registry and cursor (RO)
            try:
                registry = Registry(self.db)
                cr = registry.cursor(readonly=True)
                self.registry = registry.check_signaling(cr)
            except (AttributeError, psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
                raise RegistryError(f"Cannot get registry {self.db}") from e
            threading.current_thread().dbname = self.registry.db_name

            # find the controller endpoint to use
            self.env = odoo.api.Environment(cr, self.session.uid, self.session.context)
            try:
                rule, args = self.registry['ir.http']._match(self.httprequest.path)
            except NotFound as not_found_exc:
                # no controller endpoint matched -> fallback or 404
                serve_func = functools.partial(self._serve_ir_http_fallback, not_found_exc)
                readonly = True
            else:
                # a controller endpoint matched -> dispatch it the request
                self._set_request_dispatcher(rule)
                serve_func = functools.partial(self._serve_ir_http, rule, args)
                readonly = rule.endpoint.routing['readonly']
                if callable(readonly):
                    readonly = readonly(rule.endpoint.func.__self__, rule, args)

            # keep on using the RO cursor when a readonly route matched,
            # and for serve fallback
            if readonly and cr.readonly:
                threading.current_thread().cursor_mode = 'ro'
                try:
                    return service_model.retrying(serve_func, env=self.env)
                except psycopg2.errors.ReadOnlySqlTransaction as exc:
                    # although the controller is marked read-only, it
                    # attempted a write operation, try again using a
                    # read/write cursor
                    _logger.warning("%s, retrying with a read/write cursor", exc.args[0].rstrip(), exc_info=True)
                    threading.current_thread().cursor_mode = 'ro->rw'
                except Exception as exc:  # noqa: BLE001
                    raise self._update_served_exception(exc)
            else:
                threading.current_thread().cursor_mode = 'rw'

            # we must use a RW cursor when a read/write route matched, or
            # there was a ReadOnlySqlTransaction error
            if cr.readonly:
                cr.close()
                cr = self.env.registry.cursor()
            else:
                # the cursor is already a RW cursor, start a new transaction
                # that will avoid repeatable read serialization errors because
                # check signaling is not done in `retrying` and that function
                # would just succeed the second time
                cr.rollback()
            assert not cr.readonly
            self.env = self.env(cr=cr)
            try:
                return service_model.retrying(serve_func, env=self.env)
            except Exception as exc:  # noqa: BLE001
                raise self._update_served_exception(exc)
        except HTTPException as exc:
            if exc.code is not None:
                raise
            # Valid response returned via werkzeug.exceptions.abort
            response = exc.get_response()
            HttpDispatcher(self).post_dispatch(response)
            return response
        finally:
            self.env = None
            if cr is not None:
                cr.close()