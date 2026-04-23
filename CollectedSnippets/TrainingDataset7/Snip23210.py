def test_nested_choices_without_id(self):
        nested_choices = (
            ("unknown", "Unknown"),
            ("Audio", (("vinyl", "Vinyl"), ("cd", "CD"))),
            ("Video", (("vhs", "VHS"), ("dvd", "DVD"))),
        )
        html = """
        <div>
        <div> <label>
        <input type="checkbox" name="nestchoice" value="unknown"> Unknown</label></div>
        <div>
        <label>Audio</label>
        <div> <label>
        <input checked type="checkbox" name="nestchoice" value="vinyl"> Vinyl
        </label></div>
        <div> <label>
        <input type="checkbox" name="nestchoice" value="cd"> CD</label></div>
        </div><div>
        <label>Video</label>
        <div> <label>
        <input type="checkbox" name="nestchoice" value="vhs"> VHS</label></div>
        <div> <label>
        <input type="checkbox" name="nestchoice" value="dvd"checked> DVD</label></div>
        </div>
        </div>
        """
        self.check_html(
            self.widget(choices=nested_choices),
            "nestchoice",
            ("vinyl", "dvd"),
            html=html,
        )