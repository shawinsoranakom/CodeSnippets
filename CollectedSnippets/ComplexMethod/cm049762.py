def __init__(self, user, allowed, /, *, partners=None, partner_emails=None, add_mention_token=False, route_kw=None,
                 exp_author=None, exp_partners=None, exp_emails=None):
        self.user = user if user._name == "res.users" else user.env.ref("base.public_user")
        self.guest = user if user._name == "mail.guest" else user.env["mail.guest"]
        self.allowed = allowed
        self.route_kw = {
            "context": {"mail_post_autofollow_author_skip": True, "mail_post_autofollow": False},
            **(route_kw or {}),
        }
        self.post_data = {
            "body": "<p>Hello</p>",
            "message_type": "comment",
            "subtype_xmlid": "mail.mt_comment",
        }
        if partner_emails is not None:
            self.post_data["partner_emails"] = partner_emails
        if partners is not None:
            self.post_data["partner_ids"] = partners.ids
        if add_mention_token:
            self.post_data["partner_ids_mention_token"] = {
                partner.id: partner._get_mention_token() for partner in partners
            }
        self.exp_author = exp_author
        self.exp_partners = exp_partners
        self.exp_emails = exp_emails