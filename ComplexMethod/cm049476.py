def _prepare_open_forum_user(self, user, forums, **kwargs):
        Post = request.env['forum.post']
        Vote = request.env['forum.post.vote']
        Activity = request.env['mail.message']
        Followers = request.env['mail.followers']
        Data = request.env["ir.model.data"]
        search_values = {}

        # questions and answers by user
        question_base_domain = Domain([
            ('parent_id', '=', False),
            ('forum_id', 'in', forums.ids), ('create_uid', '=', user.id)])
        question_domain = question_base_domain
        if search_question := kwargs.get('activity_search_question'):
            search_values['activity_search_question'] = search_question
            question_domain &= Domain.OR([
                [('name', 'ilike', search_question)],
                [('plain_content', 'ilike', search_question)]])
        user_question_ids = Post.search(question_domain, order='create_date desc')
        count_user_questions = len(user_question_ids)
        min_karma_unlink = min(forums.mapped('karma_unlink_all'))

        # limit length of visible posts by default for performance reasons, except for the high
        # karma users (not many of them, and they need it to properly moderate the forum)
        post_display_limit = None
        if request.env.user.karma < min_karma_unlink:
            post_display_limit = 20

        user_questions = user_question_ids[:post_display_limit]
        answer_base_domain = Domain([
            ('parent_id', '!=', False),
            ('forum_id', 'in', forums.ids), ('create_uid', '=', user.id)])
        answer_domain = answer_base_domain
        if search_answer := kwargs.get('activity_search_answer'):
            search_values['activity_search_answer'] = search_answer
            answer_domain &= Domain.OR([
                [('name', 'ilike', search_answer)],
                [('plain_content', 'ilike', search_answer)]])
        user_answer_ids = Post.search(answer_domain, order='create_date desc')
        count_user_answers = len(user_answer_ids)
        user_answers = user_answer_ids[:post_display_limit]

        # showing questions which user following
        post_ids = [follower.res_id for follower in Followers.sudo().search(
            [('res_model', '=', 'forum.post'), ('partner_id', '=', user.partner_id.id)])]
        followed = Post.search([('id', 'in', post_ids), ('forum_id', 'in', forums.ids), ('parent_id', '=', False)])

        # showing Favourite questions of user.
        favourite = Post.search(
            [('favourite_ids', '=', user.id), ('forum_id', 'in', forums.ids), ('parent_id', '=', False)])

        # votes which given on users questions and answers.
        data = Vote._read_group(
            [('forum_id', 'in', forums.ids), ('recipient_id', '=', user.id)], ['vote'], aggregates=['__count']
        )
        up_votes, down_votes = 0, 0
        for vote, count in data:
            if vote == '1':
                up_votes = count
            elif vote == '-1':
                down_votes = count

        # Votes which given by users on others questions and answers.
        vote_ids = Vote.search([('user_id', '=', user.id), ('forum_id', 'in', forums.ids)])

        # activity by user.
        comment = Data._xmlid_lookup('mail.mt_comment')[1]
        activities = Activity.search(
            [('res_id', 'in', Post._search(Domain.OR([question_base_domain, answer_base_domain]))),
             ('model', '=', 'forum.post'),
             ('subtype_id', '!=', comment)],
            order='date DESC', limit=100)

        posts = {}
        for act in activities:
            posts[act.res_id] = True
        posts_ids = Post.search([('id', 'in', list(posts))])
        posts = {x.id: (x.parent_id or x, x.parent_id and x or False) for x in posts_ids}

        if user != request.env.user:
            kwargs['users'] = True

        if search_question:
            activities_active_tab = 'question'
        elif search_answer:
            activities_active_tab = 'answer'
        else:
            activities_active_tab = 'activity' if request.env.user == user else 'question'
        values = {
            'uid': request.env.user.id,
            'user': user,
            'main_object': user,
            'searches': kwargs,
            'questions': user_questions,
            'count_questions': count_user_questions,
            'answers': user_answers,
            'count_answers': count_user_answers,
            'followed': followed,
            'favourite': favourite,
            'up_votes': up_votes,
            'down_votes': down_votes,
            'activities': activities,
            'activities_active_tab': activities_active_tab,
            'posts': posts,
            'vote_post': vote_ids,
            'is_profile_page': True,
            'badge_category': 'forum',
        }
        values.update(search_values)
        if search_values:
            values['active_tab'] = 'activities'

        return values