def event_track_proposal_post(self, event, **post):
        if not event.can_access_from_current_website():
            return json.dumps({'error': 'forbidden'})

        # Only accept existing tag indices. Use search instead of browse + exists:
        # this prevents users to register colorless tags if not allowed to (ACL).
        input_tag_indices = [int(tag_id) for tag_id in post['tags'].split(',') if tag_id]
        valid_tag_indices = request.env['event.track.tag'].search([('id', 'in', input_tag_indices)]).ids

        contact = request.env['res.partner']
        visitor_partner = request.env['website.visitor']._get_visitor_from_request().partner_id
        # Contact name is required. Therefore, empty contacts are not considered here. At least one of contact_phone
        # and contact_email must be filled. Email is verified. If the post tries to create contact with no valid entry,
        # raise exception. If normalized email is the same as logged partner, use its partner_id on track instead.
        # This prevents contact duplication. Otherwise, create new contact with contact additional info of post.
        if post.get('add_contact_information'):
            valid_contact_email = tools.email_normalize(post.get('contact_email'))
            # Here, the phone is not formatted. To format it, one needs a country. Based on a country, from geoip for instance.
            # The problem is that one could propose a track in country A with phone number of country B. Validity is therefore
            # quite tricky. We accept any format of contact_phone. Could be improved with select country phone widget.
            if valid_contact_email or post.get('contact_phone'):
                if visitor_partner and valid_contact_email == visitor_partner.email_normalized:
                    contact = visitor_partner
                else:
                    contact = request.env['res.partner'].sudo().create({
                        'email': valid_contact_email,
                        'name': post.get('contact_name'),
                        'phone': post.get('contact_phone'),
                    })
            else:
                return json.dumps({'error': 'invalidFormInputs'})
        # If the speaker email is the same as logged user's, then also uses its partner on track, same as above.
        else:
            valid_speaker_email = tools.email_normalize(post['partner_email'])
            if visitor_partner and valid_speaker_email == visitor_partner.email_normalized:
                contact = visitor_partner

        track = request.env['event.track'].with_context({'mail_create_nosubscribe': True}).sudo().create({
            'name': post['track_name'],
            'partner_id': contact.id,
            'partner_name': post['partner_name'],
            'partner_email': post['partner_email'],
            'partner_phone': post['partner_phone'],
            'partner_function': post['partner_function'],
            'contact_phone': contact.phone,
            'contact_email': contact.email,
            'event_id': event.id,
            'tag_ids': [(6, 0, valid_tag_indices)],
            'description': plaintext2html(post['description']),
            'partner_biography': plaintext2html(post['partner_biography']),
            'user_id': False,
            'image': base64.b64encode(post['image'].read()) if post.get('image') else False,
        })

        if request.env.user != request.website.user_id:
            track.sudo().message_subscribe(partner_ids=request.env.user.partner_id.ids)

        return json.dumps({'success': True})