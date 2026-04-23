async def test_save_as_pdf_param_model_schema(self):
		"""SaveAsPdfAction schema exposes the right fields with defaults."""
		from browser_use.tools.views import SaveAsPdfAction

		schema = SaveAsPdfAction.model_json_schema()
		props = schema['properties']

		assert 'file_name' in props
		assert 'print_background' in props
		assert 'landscape' in props
		assert 'scale' in props
		assert 'paper_format' in props

		# Check defaults
		assert props['print_background']['default'] is True
		assert props['landscape']['default'] is False
		assert props['scale']['default'] == 1.0
		assert props['paper_format']['default'] == 'Letter'