def test_data_model_ref_when_model_name_is_camel_case(self):
        rel = VideoStream._meta.get_field("release_event").remote_field
        widget = forms.Select()
        wrapper = widgets.RelatedFieldWidgetWrapper(widget, rel, widget_admin_site)
        self.assertIs(wrapper.is_hidden, False)
        context = wrapper.get_context("release_event", None, {})
        self.assertEqual(context["model"], "release event")
        self.assertEqual(context["model_name"], "releaseevent")
        output = wrapper.render("stream", "value")
        expected = """
        <div class="related-widget-wrapper" data-model-ref="releaseevent">
          <select name="stream" data-context="available-source">
          </select>
          <a class="related-widget-wrapper-link add-related" id="add_id_stream"
             data-popup="yes" title="Add another release event"
             href="/admin_widgets/releaseevent/add/?_to_field=album&amp;_popup=1&_source_model=admin_widgets.videostream">
            <img src="/static/admin/img/icon-addlink.svg" alt="" width="24" height="24">
          </a>
        </div>
        """
        self.assertHTMLEqual(output, expected)