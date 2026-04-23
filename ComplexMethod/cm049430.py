def _compute_quiz_data(self):
        tracks_quiz = self.filtered(lambda track: track.quiz_id)
        (self - tracks_quiz).is_quiz_completed = False
        (self - tracks_quiz).quiz_points = 0
        if tracks_quiz:
            current_visitor = self.env['website.visitor']._get_visitor_from_request()
            if self.env.user._is_public() and not current_visitor:
                for track in tracks_quiz:
                    track.is_quiz_completed = False
                    track.quiz_points = 0
            else:
                if self.env.user._is_public():
                    domain = [('visitor_id', '=', current_visitor.id)]
                elif current_visitor:
                    domain = [
                        '|',
                        ('partner_id', '=', self.env.user.partner_id.id),
                        ('visitor_id', '=', current_visitor.id)
                    ]
                else:
                    domain = [('partner_id', '=', self.env.user.partner_id.id)]

                event_track_visitors = self.env['event.track.visitor'].sudo().search_read(
                    Domain.AND([
                        domain,
                        [('track_id', 'in', tracks_quiz.ids)]
                    ]), fields=['track_id', 'quiz_completed', 'quiz_points']
                )

                quiz_visitor_map = {
                    track_visitor['track_id'][0]: {
                        'quiz_completed': track_visitor['quiz_completed'],
                        'quiz_points': track_visitor['quiz_points']
                    } for track_visitor in event_track_visitors
                }
                for track in tracks_quiz:
                    if quiz_visitor_map.get(track.id):
                        track.is_quiz_completed = quiz_visitor_map[track.id]['quiz_completed']
                        track.quiz_points = quiz_visitor_map[track.id]['quiz_points']
                    else:
                        track.is_quiz_completed = False
                        track.quiz_points = 0