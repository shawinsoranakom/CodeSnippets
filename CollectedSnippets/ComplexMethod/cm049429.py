def _get_leaderboard(self, event, searched_name=None):
        current_visitor = request.env['website.visitor']._get_visitor_from_request()
        track_visitor_data = request.env['event.track.visitor'].sudo()._read_group(
            [('track_id', 'in', event.track_ids.ids),
             ('visitor_id', '!=', False),
             ('quiz_points', '>', 0)],
            ['visitor_id'],
            ['quiz_points:sum'], order='quiz_points:sum DESC, visitor_id ASC')
        data_map = {visitor.id: points for visitor, points in track_visitor_data}
        leaderboard = []
        position = 1
        current_visitor_position = False
        visitors_by_id = {
            visitor.id: visitor
            for visitor in request.env['website.visitor'].sudo().browse(data_map.keys())
        }
        for visitor_id, points in data_map.items():
            visitor = visitors_by_id.get(visitor_id)
            if not visitor:
                continue
            if (searched_name and searched_name.lower() in visitor.display_name.lower()) or not searched_name:
                leaderboard.append({'visitor': visitor, 'points': points, 'position': position})
                if current_visitor and current_visitor == visitor:
                    current_visitor_position = position
            position = position + 1

        return {
            'top3_visitors': leaderboard[:3],
            'visitors': leaderboard,
            'current_visitor_position': current_visitor_position,
            'current_visitor': current_visitor,
            'searched_name': searched_name
        }