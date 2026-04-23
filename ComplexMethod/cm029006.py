def test_serialize_user_message_text_parts(self):
		"""Test serializing a user message with text content parts."""
		message = UserMessage(
			content=[
				ContentPartTextParam(type='text', text='First part'),
				ContentPartTextParam(type='text', text='Second part'),
			]
		)
		result = ResponsesAPIMessageSerializer.serialize(message)

		assert result['role'] == 'user'
		assert isinstance(result['content'], list)
		assert len(result['content']) == 2
		assert result['content'][0]['type'] == 'input_text'
		assert result['content'][0]['text'] == 'First part'
		assert result['content'][1]['type'] == 'input_text'
		assert result['content'][1]['text'] == 'Second part'