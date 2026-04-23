def _get_slide_quiz_data(self, slide):
        is_designer = request.env.user.has_group('website.group_website_designer')
        slides_resources = slide.slide_resource_ids if slide.channel_id.is_member else []
        values = {
            'slide_description': slide.description,
            'slide_questions': [{
                'answer_ids': [{
                    'comment': answer.comment if is_designer else None,
                    'id': answer.id,
                    'is_correct': answer.is_correct if slide.user_has_completed or is_designer else None,
                    'text_value': answer.text_value,
                } for answer in question.sudo().answer_ids],
                'id': question.id,
                'question': question.question,
            } for question in slide.question_ids],
            'slide_resource_ids': [{
                'display_name' : resource.display_name,
                'download_url': resource.download_url,
                'id': resource.id,
                'link': resource.link,
                'resource_type': resource.resource_type,
            } for resource in slides_resources]
        }
        if 'slide_answer_quiz' in request.session:
            slide_answer_quiz = json.loads(request.session['slide_answer_quiz'])
            if str(slide.id) in slide_answer_quiz:
                values['session_answers'] = slide_answer_quiz[str(slide.id)]
        values.update(self._get_slide_quiz_partner_info(slide))
        return values