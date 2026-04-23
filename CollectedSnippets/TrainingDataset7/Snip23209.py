def test_nested_choices(self):
        nested_choices = (
            ("unknown", "Unknown"),
            ("Audio", (("vinyl", "Vinyl"), ("cd", "CD"))),
            ("Video", (("vhs", "VHS"), ("dvd", "DVD"))),
        )
        html = """
        <div id="media">
        <div> <label for="media_0">
        <input type="checkbox" name="nestchoice" value="unknown" id="media_0"> Unknown
        </label></div>
        <div>
        <label>Audio</label>
        <div> <label for="media_1_0">
        <input checked type="checkbox" name="nestchoice" value="vinyl" id="media_1_0">
        Vinyl</label></div>
        <div> <label for="media_1_1">
        <input type="checkbox" name="nestchoice" value="cd" id="media_1_1"> CD
        </label></div>
        </div><div>
        <label>Video</label>
        <div> <label for="media_2_0">
        <input type="checkbox" name="nestchoice" value="vhs" id="media_2_0"> VHS
        </label></div>
        <div> <label for="media_2_1">
        <input type="checkbox" name="nestchoice" value="dvd" id="media_2_1" checked> DVD
        </label></div>
        </div>
        </div>
        """
        self.check_html(
            self.widget(choices=nested_choices),
            "nestchoice",
            ("vinyl", "dvd"),
            attrs={"id": "media"},
            html=html,
        )