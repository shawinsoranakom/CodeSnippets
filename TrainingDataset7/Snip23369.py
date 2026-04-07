def test_selectdate_empty_label(self):
        w = SelectDateWidget(years=("2014",), empty_label="empty_label")

        # Rendering the default state with empty_label set as string.
        self.assertInHTML(
            '<option selected value="">empty_label</option>',
            w.render("mydate", ""),
            count=3,
        )

        w = SelectDateWidget(
            years=("2014",), empty_label=("empty_year", "empty_month", "empty_day")
        )

        # Rendering the default state with empty_label tuple.
        self.assertHTMLEqual(
            w.render("mydate", ""),
            """
            <select name="mydate_month" id="id_mydate_month">
                <option selected value="">empty_month</option>
                <option value="1">January</option>
                <option value="2">February</option>
                <option value="3">March</option>
                <option value="4">April</option>
                <option value="5">May</option>
                <option value="6">June</option>
                <option value="7">July</option>
                <option value="8">August</option>
                <option value="9">September</option>
                <option value="10">October</option>
                <option value="11">November</option>
                <option value="12">December</option>
            </select>

            <select name="mydate_day" id="id_mydate_day">
                <option selected value="">empty_day</option>
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
                <option value="13">13</option>
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

            <select name="mydate_year" id="id_mydate_year">
                <option selected value="">empty_year</option>
                <option value="2014">2014</option>
            </select>
            """,
        )

        with self.assertRaisesMessage(
            ValueError, "empty_label list/tuple must have 3 elements."
        ):
            SelectDateWidget(years=("2014",), empty_label=("not enough", "values"))