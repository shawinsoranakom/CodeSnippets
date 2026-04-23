def _notify_state_update(self):
        for post in self:
            tag_partners = post.tag_ids.sudo().mapped('message_partner_ids')

            if post.state == 'active' and post.parent_id:
                post.parent_id.message_post_with_source(
                    'website_forum.forum_post_template_new_answer',
                    subject=_('Re: %s', post.parent_id.name),
                    partner_ids=tag_partners.ids,
                    subtype_xmlid='website_forum.mt_answer_new',
                )
            elif post.state == 'active' and not post.parent_id:
                post.message_post_with_source(
                    'website_forum.forum_post_template_new_question',
                    subject=post.name,
                    partner_ids=tag_partners.ids,
                    subtype_xmlid='website_forum.mt_question_new',
                )
            elif post.state == 'pending' and not post.parent_id:
                # TDE FIXME: in master, you should probably use a subtype;
                # however here we remove subtype but set partner_ids
                partners = post.sudo().message_partner_ids | tag_partners
                partners = partners.filtered(lambda partner: partner.user_ids and any(user.karma >= post.forum_id.karma_moderate for user in partner.user_ids))

                post.message_post_with_source(
                    'website_forum.forum_post_template_validation',
                    subject=post.name,
                    partner_ids=partners.ids,
                    subtype_xmlid='mail.mt_note',
                )
        return True