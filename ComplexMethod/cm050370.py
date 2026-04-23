def create_slide(self, *args, **post):
        create_new_survey = post['slide_category'] == "certification" and post.get('survey') and not post['survey']['id']
        linked_survey_id = int(post.get('survey', {}).get('id') or 0)

        if create_new_survey:
            # If user cannot create a new survey, no need to create the slide either.
            if not request.env['survey.survey'].has_access('create'):
                return {'error': _('You are not allowed to create a survey.')}

            # Create survey first as certification slide needs a survey_id (constraint)
            post['survey_id'] = request.env['survey.survey'].create({
                'title': post['survey']['title'],
                'questions_layout': 'page_per_question',
                'is_attempts_limited': True,
                'attempts_limit': 1,
                'is_time_limited': False,
                'scoring_type': 'scoring_without_answers',
                'certification': True,
                'scoring_success_min': 70.0,
                'certification_mail_template_id': request.env.ref('survey.mail_template_certification').id,
            }).id
        elif linked_survey_id:
            try:
                request.env['survey.survey'].browse([linked_survey_id]).read(['title'])
            except AccessError:
                return {'error': _('You are not allowed to link a certification.')}

            post['survey_id'] = post['survey']['id']

        # Then create the slide
        result = super(WebsiteSlidesSurvey, self).create_slide(*args, **post)

        if post['slide_category'] == "certification":
            # Set the url to redirect the user to the survey
            slide = request.env['slide.slide'].browse(result['slide_id'])
            result['url'] = f'/slides/slide/{request.env["ir.http"]._slug(slide)}?fullscreen=1'

        return result