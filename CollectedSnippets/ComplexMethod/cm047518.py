def __call__(
        self,
        cr: BaseCursor | None = None,
        user: IdType | BaseModel | None = None,
        context: dict | None = None,
        su: bool | None = None,
    ) -> Environment:
        """ Return an environment based on ``self`` with modified parameters.

        :param cr: optional database cursor to change the current cursor
        :type cursor: :class:`~odoo.sql_db.Cursor`
        :param user: optional user/user id to change the current user
        :type user: int or :class:`res.users record<~odoo.addons.base.models.res_users.ResUsers>`
        :param dict context: optional context dictionary to change the current context
        :param bool su: optional boolean to change the superuser mode
        :returns: environment with specified args (new or existing one)
        """
        cr = self.cr if cr is None else cr
        uid = self.uid if user is None else int(user)  # type: ignore
        if context is None:
            context = clean_context(self.context) if su and not self.su else self.context
        su = (user is None and self.su) if su is None else su
        return Environment(cr, uid, context, su)