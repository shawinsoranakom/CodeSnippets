def test_l10n(self):
        w = SelectDateWidget(
            years=(
                "2007",
                "2008",
                "2009",
                "2010",
                "2011",
                "2012",
                "2013",
                "2014",
                "2015",
                "2016",
            )
        )
        self.assertEqual(
            w.value_from_datadict(
                {"date_year": "2010", "date_month": "8", "date_day": "13"}, {}, "date"
            ),
            "13-08-2010",
        )

        self.assertHTMLEqual(
            w.render("date", "13-08-2010"),
            """
            <select name="date_day" id="id_date_day">
                <option value="">---</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
                <option value="7">7</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11">11</option>
                <option value="12">12</option>
                <option value="13" selected>13</option>
                <option value="14">14</option>
                <option value="15">15</option>
                <option value="16">16</option>
                <option value="17">17</option>
                <option value="18">18</option>
                <option value="19">19</option>
                <option value="20">20</option>
                <option value="21">21</option>
                <option value="22">22</option>
                <option value="23">23</option>
                <option value="24">24</option>
                <option value="25">25</option>
                <option value="26">26</option>
                <option value="27">27</option>
                <option value="28">28</option>
                <option value="29">29</option>
                <option value="30">30</option>
                <option value="31">31</option>
            </select>

            <select name="date_month" id="id_date_month">
                <option value="">---</option>
                <option value="1">januari</option>
                <option value="2">februari</option>
                <option value="3">maart</option>
                <option value="4">april</option>
                <option value="5">mei</option>
                <option value="6">juni</option>
                <option value="7">juli</option>
                <option value="8" selected>augustus</option>
                <option value="9">september</option>
                <option value="10">oktober</option>
                <option value="11">november</option>
                <option value="12">december</option>
            </select>

            <select name="date_year" id="id_date_year">
                <option value="">---</option>
                <option value="2007">2007</option>
                <option value="2008">2008</option>
                <option value="2009">2009</option>
                <option value="2010" selected>2010</option>
                <option value="2011">2011</option>
                <option value="2012">2012</option>
                <option value="2013">2013</option>
                <option value="2014">2014</option>
                <option value="2015">2015</option>
                <option value="2016">2016</option>
            </select>
            """,
        )

        # Even with an invalid date, the widget should reflect the entered
        # value.
        self.assertEqual(w.render("mydate", "2010-02-30").count("selected"), 3)

        # Years before 1900 should work.
        w = SelectDateWidget(years=("1899",))
        self.assertEqual(
            w.value_from_datadict(
                {"date_year": "1899", "date_month": "8", "date_day": "13"}, {}, "date"
            ),
            "13-08-1899",
        )
        # And years before 1000 (demonstrating the need for
        # sanitize_strftime_format).
        w = SelectDateWidget(years=("0001",))
        self.assertEqual(
            w.value_from_datadict(
                {"date_year": "0001", "date_month": "8", "date_day": "13"}, {}, "date"
            ),
            "13-08-0001",
        )