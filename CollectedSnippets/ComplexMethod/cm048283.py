def _chatbot_prepare_customer_values(self, discuss_channel, create_partner=True, update_partner=True):
        """ Common method that allows retreiving default customer values from the discuss.channel
        following a chatbot.script.

        This method will return a dict containing the 'customer' values such as:
        {
            'partner': The created partner (see 'create_partner') or the partner from the
              environment if not public
            'email': The email extracted from the discuss.channel messages
              (see step_type 'question_email')
            'phone': The phone extracted from the discuss.channel messages
              (see step_type 'question_phone')
            'description': A default description containing the "Please contact me on" and "Please
              call me on" with the related email and phone numbers.
              Can be used as a default description to create leads or tickets for example.
        }

        :param record discuss_channel: the discuss.channel holding the visitor's conversation with the bot.
        :param bool create_partner: whether or not to create a res.partner is the current user is public.
          Defaults to True.
        :param bool update_partner: whether or not to set update the email and phone on the res.partner
          from the environment (if not a public user) if those are not set yet. Defaults to True.

        :returns: a dict containing the customer values."""

        partner = False
        user_inputs = discuss_channel._chatbot_find_customer_values_in_messages({
            'question_email': 'email',
            'question_phone': 'phone',
        })
        input_email = user_inputs.get('email', False)
        input_phone = user_inputs.get('phone', False)

        if self.env.user._is_public() and create_partner:
            partner = self.env['res.partner'].create({
                'name': input_email,
                'email': input_email,
                'phone': input_phone,
            })
        elif not self.env.user._is_public():
            partner = self.env.user.partner_id
            if update_partner:
                # update email/phone value from partner if not set
                update_values = {}
                if input_email and not partner.email:
                    update_values['email'] = input_email
                if input_phone and not partner.phone:
                    update_values['phone'] = input_phone
                if update_values:
                    partner.write(update_values)

        description = Markup('')
        if input_email:
            description += Markup("%s<strong>%s</strong><br>") % (_("Email: "), input_email)
        if input_phone:
            description += Markup("%s<strong>%s</strong><br>") % (_("Phone: "), input_phone)
        if description:
            description += Markup('<br>')

        return {
            'partner': partner,
            'email': input_email,
            'phone': input_phone,
            'description': description,
        }