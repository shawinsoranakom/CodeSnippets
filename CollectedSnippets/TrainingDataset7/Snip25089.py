def test_l10n_enabled(self):
        self.maxDiff = 3000
        # Catalan locale
        with translation.override("ca", deactivate=True):
            self.assertEqual(r"j E \d\e Y", get_format("DATE_FORMAT"))
            self.assertEqual(1, get_format("FIRST_DAY_OF_WEEK"))
            self.assertEqual(",", get_format("DECIMAL_SEPARATOR"))
            self.assertEqual("10:15", time_format(self.t))
            self.assertEqual("31 desembre de 2009", date_format(self.d))
            self.assertEqual("1 abril de 2009", date_format(datetime.date(2009, 4, 1)))
            self.assertEqual(
                "desembre del 2009", date_format(self.d, "YEAR_MONTH_FORMAT")
            )
            self.assertEqual(
                "31/12/2009 20:50", date_format(self.dt, "SHORT_DATETIME_FORMAT")
            )
            self.assertEqual("No localizable", localize("No localizable"))

            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual("66.666,666", localize(self.n))
                self.assertEqual("99.999,999", localize(self.f))
                self.assertEqual("10.000", localize(self.long))
                self.assertEqual("True", localize(True))

            with self.settings(USE_THOUSAND_SEPARATOR=False):
                self.assertEqual("66666,666", localize(self.n))
                self.assertEqual("99999,999", localize(self.f))
                self.assertEqual("10000", localize(self.long))
                self.assertEqual("31 desembre de 2009", localize(self.d))
                self.assertEqual("31 desembre de 2009 a les 20:50", localize(self.dt))

            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual("66.666,666", Template("{{ n }}").render(self.ctxt))
                self.assertEqual("99.999,999", Template("{{ f }}").render(self.ctxt))
                self.assertEqual("10.000", Template("{{ l }}").render(self.ctxt))

            with self.settings(USE_THOUSAND_SEPARATOR=True):
                form3 = I18nForm(
                    {
                        "decimal_field": "66.666,666",
                        "float_field": "99.999,999",
                        "date_field": "31/12/2009",
                        "datetime_field": "31/12/2009 20:50",
                        "time_field": "20:50",
                        "integer_field": "1.234",
                    }
                )
                self.assertTrue(form3.is_valid())
                self.assertEqual(
                    decimal.Decimal("66666.666"), form3.cleaned_data["decimal_field"]
                )
                self.assertEqual(99999.999, form3.cleaned_data["float_field"])
                self.assertEqual(
                    datetime.date(2009, 12, 31), form3.cleaned_data["date_field"]
                )
                self.assertEqual(
                    datetime.datetime(2009, 12, 31, 20, 50),
                    form3.cleaned_data["datetime_field"],
                )
                self.assertEqual(
                    datetime.time(20, 50), form3.cleaned_data["time_field"]
                )
                self.assertEqual(1234, form3.cleaned_data["integer_field"])

            with self.settings(USE_THOUSAND_SEPARATOR=False):
                self.assertEqual("66666,666", Template("{{ n }}").render(self.ctxt))
                self.assertEqual("99999,999", Template("{{ f }}").render(self.ctxt))
                self.assertEqual(
                    "31 desembre de 2009", Template("{{ d }}").render(self.ctxt)
                )
                self.assertEqual(
                    "31 desembre de 2009 a les 20:50",
                    Template("{{ dt }}").render(self.ctxt),
                )
                self.assertEqual(
                    "66666,67", Template("{{ n|floatformat:2 }}").render(self.ctxt)
                )
                self.assertEqual(
                    "100000,0", Template("{{ f|floatformat }}").render(self.ctxt)
                )
                self.assertEqual(
                    "66.666,67",
                    Template('{{ n|floatformat:"2g" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "100.000,0",
                    Template('{{ f|floatformat:"g" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "10:15", Template('{{ t|time:"TIME_FORMAT" }}').render(self.ctxt)
                )
                self.assertEqual(
                    "31/12/2009",
                    Template('{{ d|date:"SHORT_DATE_FORMAT" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "31/12/2009 20:50",
                    Template('{{ dt|date:"SHORT_DATETIME_FORMAT" }}').render(self.ctxt),
                )
                self.assertEqual(
                    date_format(datetime.datetime.now()),
                    Template('{% now "DATE_FORMAT" %}').render(self.ctxt),
                )

            with self.settings(USE_THOUSAND_SEPARATOR=False):
                form4 = I18nForm(
                    {
                        "decimal_field": "66666,666",
                        "float_field": "99999,999",
                        "date_field": "31/12/2009",
                        "datetime_field": "31/12/2009 20:50",
                        "time_field": "20:50",
                        "integer_field": "1234",
                    }
                )
                self.assertTrue(form4.is_valid())
                self.assertEqual(
                    decimal.Decimal("66666.666"), form4.cleaned_data["decimal_field"]
                )
                self.assertEqual(99999.999, form4.cleaned_data["float_field"])
                self.assertEqual(
                    datetime.date(2009, 12, 31), form4.cleaned_data["date_field"]
                )
                self.assertEqual(
                    datetime.datetime(2009, 12, 31, 20, 50),
                    form4.cleaned_data["datetime_field"],
                )
                self.assertEqual(
                    datetime.time(20, 50), form4.cleaned_data["time_field"]
                )
                self.assertEqual(1234, form4.cleaned_data["integer_field"])

            form5 = SelectDateForm(
                {
                    "date_field_month": "12",
                    "date_field_day": "31",
                    "date_field_year": "2009",
                }
            )
            self.assertTrue(form5.is_valid())
            self.assertEqual(
                datetime.date(2009, 12, 31), form5.cleaned_data["date_field"]
            )
            self.assertHTMLEqual(
                '<select name="mydate_day" id="id_mydate_day">'
                '<option value="">---</option>'
                '<option value="1">1</option>'
                '<option value="2">2</option>'
                '<option value="3">3</option>'
                '<option value="4">4</option>'
                '<option value="5">5</option>'
                '<option value="6">6</option>'
                '<option value="7">7</option>'
                '<option value="8">8</option>'
                '<option value="9">9</option>'
                '<option value="10">10</option>'
                '<option value="11">11</option>'
                '<option value="12">12</option>'
                '<option value="13">13</option>'
                '<option value="14">14</option>'
                '<option value="15">15</option>'
                '<option value="16">16</option>'
                '<option value="17">17</option>'
                '<option value="18">18</option>'
                '<option value="19">19</option>'
                '<option value="20">20</option>'
                '<option value="21">21</option>'
                '<option value="22">22</option>'
                '<option value="23">23</option>'
                '<option value="24">24</option>'
                '<option value="25">25</option>'
                '<option value="26">26</option>'
                '<option value="27">27</option>'
                '<option value="28">28</option>'
                '<option value="29">29</option>'
                '<option value="30">30</option>'
                '<option value="31" selected>31</option>'
                "</select>"
                '<select name="mydate_month" id="id_mydate_month">'
                '<option value="">---</option>'
                '<option value="1">gener</option>'
                '<option value="2">febrer</option>'
                '<option value="3">mar\xe7</option>'
                '<option value="4">abril</option>'
                '<option value="5">maig</option>'
                '<option value="6">juny</option>'
                '<option value="7">juliol</option>'
                '<option value="8">agost</option>'
                '<option value="9">setembre</option>'
                '<option value="10">octubre</option>'
                '<option value="11">novembre</option>'
                '<option value="12" selected>desembre</option>'
                "</select>"
                '<select name="mydate_year" id="id_mydate_year">'
                '<option value="">---</option>'
                '<option value="2009" selected>2009</option>'
                '<option value="2010">2010</option>'
                '<option value="2011">2011</option>'
                '<option value="2012">2012</option>'
                '<option value="2013">2013</option>'
                '<option value="2014">2014</option>'
                '<option value="2015">2015</option>'
                '<option value="2016">2016</option>'
                '<option value="2017">2017</option>'
                '<option value="2018">2018</option>'
                "</select>",
                forms.SelectDateWidget(years=range(2009, 2019)).render(
                    "mydate", datetime.date(2009, 12, 31)
                ),
            )

        # Russian locale (with E as month)
        with translation.override("ru", deactivate=True):
            self.assertHTMLEqual(
                '<select name="mydate_day" id="id_mydate_day">'
                '<option value="">---</option>'
                '<option value="1">1</option>'
                '<option value="2">2</option>'
                '<option value="3">3</option>'
                '<option value="4">4</option>'
                '<option value="5">5</option>'
                '<option value="6">6</option>'
                '<option value="7">7</option>'
                '<option value="8">8</option>'
                '<option value="9">9</option>'
                '<option value="10">10</option>'
                '<option value="11">11</option>'
                '<option value="12">12</option>'
                '<option value="13">13</option>'
                '<option value="14">14</option>'
                '<option value="15">15</option>'
                '<option value="16">16</option>'
                '<option value="17">17</option>'
                '<option value="18">18</option>'
                '<option value="19">19</option>'
                '<option value="20">20</option>'
                '<option value="21">21</option>'
                '<option value="22">22</option>'
                '<option value="23">23</option>'
                '<option value="24">24</option>'
                '<option value="25">25</option>'
                '<option value="26">26</option>'
                '<option value="27">27</option>'
                '<option value="28">28</option>'
                '<option value="29">29</option>'
                '<option value="30">30</option>'
                '<option value="31" selected>31</option>'
                "</select>"
                '<select name="mydate_month" id="id_mydate_month">'
                '<option value="">---</option>'
                '<option value="1">\u042f\u043d\u0432\u0430\u0440\u044c</option>'
                '<option value="2">\u0424\u0435\u0432\u0440\u0430\u043b\u044c</option>'
                '<option value="3">\u041c\u0430\u0440\u0442</option>'
                '<option value="4">\u0410\u043f\u0440\u0435\u043b\u044c</option>'
                '<option value="5">\u041c\u0430\u0439</option>'
                '<option value="6">\u0418\u044e\u043d\u044c</option>'
                '<option value="7">\u0418\u044e\u043b\u044c</option>'
                '<option value="8">\u0410\u0432\u0433\u0443\u0441\u0442</option>'
                '<option value="9">\u0421\u0435\u043d\u0442\u044f\u0431\u0440\u044c'
                "</option>"
                '<option value="10">\u041e\u043a\u0442\u044f\u0431\u0440\u044c</option>'
                '<option value="11">\u041d\u043e\u044f\u0431\u0440\u044c</option>'
                '<option value="12" selected>\u0414\u0435\u043a\u0430\u0431\u0440\u044c'
                "</option>"
                "</select>"
                '<select name="mydate_year" id="id_mydate_year">'
                '<option value="">---</option>'
                '<option value="2009" selected>2009</option>'
                '<option value="2010">2010</option>'
                '<option value="2011">2011</option>'
                '<option value="2012">2012</option>'
                '<option value="2013">2013</option>'
                '<option value="2014">2014</option>'
                '<option value="2015">2015</option>'
                '<option value="2016">2016</option>'
                '<option value="2017">2017</option>'
                '<option value="2018">2018</option>'
                "</select>",
                forms.SelectDateWidget(years=range(2009, 2019)).render(
                    "mydate", datetime.date(2009, 12, 31)
                ),
            )

        # English locale
        with translation.override("en", deactivate=True):
            self.assertEqual("N j, Y", get_format("DATE_FORMAT"))
            self.assertEqual(0, get_format("FIRST_DAY_OF_WEEK"))
            self.assertEqual(".", get_format("DECIMAL_SEPARATOR"))
            self.assertEqual("Dec. 31, 2009", date_format(self.d))
            self.assertEqual("December 2009", date_format(self.d, "YEAR_MONTH_FORMAT"))
            self.assertEqual(
                "12/31/2009 8:50 p.m.", date_format(self.dt, "SHORT_DATETIME_FORMAT")
            )
            self.assertEqual("No localizable", localize("No localizable"))

            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual("66,666.666", localize(self.n))
                self.assertEqual("99,999.999", localize(self.f))
                self.assertEqual("10,000", localize(self.long))

            with self.settings(USE_THOUSAND_SEPARATOR=False):
                self.assertEqual("66666.666", localize(self.n))
                self.assertEqual("99999.999", localize(self.f))
                self.assertEqual("10000", localize(self.long))
                self.assertEqual("Dec. 31, 2009", localize(self.d))
                self.assertEqual("Dec. 31, 2009, 8:50 p.m.", localize(self.dt))

            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual("66,666.666", Template("{{ n }}").render(self.ctxt))
                self.assertEqual("99,999.999", Template("{{ f }}").render(self.ctxt))
                self.assertEqual("10,000", Template("{{ l }}").render(self.ctxt))

            with self.settings(USE_THOUSAND_SEPARATOR=False):
                self.assertEqual("66666.666", Template("{{ n }}").render(self.ctxt))
                self.assertEqual("99999.999", Template("{{ f }}").render(self.ctxt))
                self.assertEqual("Dec. 31, 2009", Template("{{ d }}").render(self.ctxt))
                self.assertEqual(
                    "Dec. 31, 2009, 8:50 p.m.", Template("{{ dt }}").render(self.ctxt)
                )
                self.assertEqual(
                    "66666.67", Template("{{ n|floatformat:2 }}").render(self.ctxt)
                )
                self.assertEqual(
                    "100000.0", Template("{{ f|floatformat }}").render(self.ctxt)
                )
                self.assertEqual(
                    "66,666.67",
                    Template('{{ n|floatformat:"2g" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "100,000.0",
                    Template('{{ f|floatformat:"g" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "12/31/2009",
                    Template('{{ d|date:"SHORT_DATE_FORMAT" }}').render(self.ctxt),
                )
                self.assertEqual(
                    "12/31/2009 8:50 p.m.",
                    Template('{{ dt|date:"SHORT_DATETIME_FORMAT" }}').render(self.ctxt),
                )

            form5 = I18nForm(
                {
                    "decimal_field": "66666.666",
                    "float_field": "99999.999",
                    "date_field": "12/31/2009",
                    "datetime_field": "12/31/2009 20:50",
                    "time_field": "20:50",
                    "integer_field": "1234",
                }
            )
            self.assertTrue(form5.is_valid())
            self.assertEqual(
                decimal.Decimal("66666.666"), form5.cleaned_data["decimal_field"]
            )
            self.assertEqual(99999.999, form5.cleaned_data["float_field"])
            self.assertEqual(
                datetime.date(2009, 12, 31), form5.cleaned_data["date_field"]
            )
            self.assertEqual(
                datetime.datetime(2009, 12, 31, 20, 50),
                form5.cleaned_data["datetime_field"],
            )
            self.assertEqual(datetime.time(20, 50), form5.cleaned_data["time_field"])
            self.assertEqual(1234, form5.cleaned_data["integer_field"])

            form6 = SelectDateForm(
                {
                    "date_field_month": "12",
                    "date_field_day": "31",
                    "date_field_year": "2009",
                }
            )
            self.assertTrue(form6.is_valid())
            self.assertEqual(
                datetime.date(2009, 12, 31), form6.cleaned_data["date_field"]
            )
            self.assertHTMLEqual(
                '<select name="mydate_month" id="id_mydate_month">'
                '<option value="">---</option>'
                '<option value="1">January</option>'
                '<option value="2">February</option>'
                '<option value="3">March</option>'
                '<option value="4">April</option>'
                '<option value="5">May</option>'
                '<option value="6">June</option>'
                '<option value="7">July</option>'
                '<option value="8">August</option>'
                '<option value="9">September</option>'
                '<option value="10">October</option>'
                '<option value="11">November</option>'
                '<option value="12" selected>December</option>'
                "</select>"
                '<select name="mydate_day" id="id_mydate_day">'
                '<option value="">---</option>'
                '<option value="1">1</option>'
                '<option value="2">2</option>'
                '<option value="3">3</option>'
                '<option value="4">4</option>'
                '<option value="5">5</option>'
                '<option value="6">6</option>'
                '<option value="7">7</option>'
                '<option value="8">8</option>'
                '<option value="9">9</option>'
                '<option value="10">10</option>'
                '<option value="11">11</option>'
                '<option value="12">12</option>'
                '<option value="13">13</option>'
                '<option value="14">14</option>'
                '<option value="15">15</option>'
                '<option value="16">16</option>'
                '<option value="17">17</option>'
                '<option value="18">18</option>'
                '<option value="19">19</option>'
                '<option value="20">20</option>'
                '<option value="21">21</option>'
                '<option value="22">22</option>'
                '<option value="23">23</option>'
                '<option value="24">24</option>'
                '<option value="25">25</option>'
                '<option value="26">26</option>'
                '<option value="27">27</option>'
                '<option value="28">28</option>'
                '<option value="29">29</option>'
                '<option value="30">30</option>'
                '<option value="31" selected>31</option>'
                "</select>"
                '<select name="mydate_year" id="id_mydate_year">'
                '<option value="">---</option>'
                '<option value="2009" selected>2009</option>'
                '<option value="2010">2010</option>'
                '<option value="2011">2011</option>'
                '<option value="2012">2012</option>'
                '<option value="2013">2013</option>'
                '<option value="2014">2014</option>'
                '<option value="2015">2015</option>'
                '<option value="2016">2016</option>'
                '<option value="2017">2017</option>'
                '<option value="2018">2018</option>'
                "</select>",
                forms.SelectDateWidget(years=range(2009, 2019)).render(
                    "mydate", datetime.date(2009, 12, 31)
                ),
            )