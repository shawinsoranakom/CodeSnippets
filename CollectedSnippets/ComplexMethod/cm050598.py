def _recompute_completion(self):
        """ This method computes the completion and member_status of attendees that are neither
            'invited' nor 'completed'. Indeed, once completed, membership should remain so.
            We do not do any update on the 'invited' records.
            One should first set member_status to 'joined' before recomputing those values
            when enrolling an invited or archived attendee.
            It takes into account the previous completion value to add or remove karma for
            completing the course to the attendee (see _post_completion_update_hook)
        """
        read_group_res = self.env['slide.slide.partner'].sudo()._read_group(
            ['&', '&', ('channel_id', 'in', self.mapped('channel_id').ids),
             ('partner_id', 'in', self.mapped('partner_id').ids),
             ('completed', '=', True),
             ('slide_id.is_published', '=', True),
             ('slide_id.active', '=', True)],
            ['channel_id', 'partner_id'],
            aggregates=['__count'])
        mapped_data = {
            (channel.id, partner.id): count
            for channel, partner, count in read_group_res
        }

        completed_records = self.env['slide.channel.partner']
        uncompleted_records = self.env['slide.channel.partner']
        for record in self:
            if record.member_status in ('completed', 'invited'):
                continue
            was_finished = record.completion == 100
            record.completed_slides_count = mapped_data.get((record.channel_id.id, record.partner_id.id), 0)
            record.completion = round(100.0 * record.completed_slides_count / (record.channel_id.total_slides or 1))

            if not record.channel_id.active:
                continue
            elif not was_finished and record.channel_id.total_slides and record.completed_slides_count >= record.channel_id.total_slides:
                completed_records += record
            elif was_finished and record.completed_slides_count < record.channel_id.total_slides:
                uncompleted_records += record

            if record.completion == 100:
                record.member_status = 'completed'
            elif record.completion == 0:
                record.member_status = 'joined'
            else:
                record.member_status = 'ongoing'

        if completed_records:
            completed_records._post_completion_update_hook(completed=True)
            completed_records._send_completed_mail()

        if uncompleted_records:
            uncompleted_records._post_completion_update_hook(completed=False)