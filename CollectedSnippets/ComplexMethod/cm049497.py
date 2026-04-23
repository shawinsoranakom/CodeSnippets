def _send_creation_communication(self, force_send=False):
        """
        Sends the 'At Creation' communication plan if it exist for the given coupons.
        """
        if self.env.context.get('loyalty_no_mail', False) or self.env.context.get('action_no_send_mail', False):
            return
        # Ideally one per program, but multiple is supported
        create_comm_per_program = dict()
        for program in self.program_id:
            create_comm_per_program[program] = program.communication_plan_ids.filtered(lambda c: c.trigger == 'create')
        for coupon in self:
            if not create_comm_per_program[coupon.program_id] or not coupon._mail_get_customer():
                continue
            for comm in create_comm_per_program[coupon.program_id]:
                mail_template = comm.mail_template_id
                email_values = {}
                if not mail_template.email_from:
                    # provide author_id & email_from values to ensure the email gets sent
                    author = coupon._get_mail_author()
                    email_values.update(author_id=author.id, email_from=author.email_formatted)
                mail_template.send_mail(
                    res_id=coupon.id,
                    force_send=force_send,
                    email_layout_xmlid='mail.mail_notification_light',
                    email_values=email_values,
                )