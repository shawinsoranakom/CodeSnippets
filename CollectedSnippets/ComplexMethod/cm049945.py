def wrapper(self, *args, **kwargs):
        req = request or wsrequest
        token = (
            req.cookies.get(req.env["mail.guest"]._cookie_name, "")
        )
        guest = req.env["mail.guest"]._get_guest_from_token(token)
        if guest and not guest.timezone and not req.env.cr.readonly:
            timezone = req.env["mail.guest"]._get_timezone_from_request(req)
            if timezone:
                guest._update_timezone(timezone)
        if guest:
            req.update_context(guest=guest)
            if isinstance(self, models.BaseModel):
                self = self.with_context(guest=guest)
        return func(self, *args, **kwargs)