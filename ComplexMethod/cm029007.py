def test_serialize_user_message_with_image(self):
		"""Test serializing a user message with image content."""
		message = UserMessage(
			content=[
				ContentPartTextParam(type='text', text='What is in this image?'),
				ContentPartImageParam(
					type='image_url',
					image_url=ImageURL(url='https://example.com/image.png', detail='auto'),
				),
			]
		)
		result = ResponsesAPIMessageSerializer.serialize(message)

		assert result['role'] == 'user'
		assert isinstance(result['content'], list)
		assert len(result['content']) == 2
		assert result['content'][0]['type'] == 'input_text'
		assert result['content'][1]['type'] == 'input_image'
		assert result['content'][1].get('image_url') == 'https://example.com/image.png'
		assert result['content'][1].get('detail') == 'auto'