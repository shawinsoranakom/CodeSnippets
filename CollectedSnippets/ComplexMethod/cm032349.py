def _run(self, history, **kwargs):
        if self.check_if_canceled("TuShare processing"):
            return

        ans = self.get_input()
        ans = ",".join(ans["content"]) if "content" in ans else ""
        if not ans:
            return TuShare.be_output("")

        try:
            if self.check_if_canceled("TuShare processing"):
                return

            tus_res = []
            params = {
                "api_name": "news",
                "token": self._param.token,
                "params": {"src": self._param.src, "start_date": self._param.start_date,
                           "end_date": self._param.end_date}
            }
            response = requests.post(url="http://api.tushare.pro", data=json.dumps(params).encode('utf-8'))
            response = response.json()
            if self.check_if_canceled("TuShare processing"):
                return
            if response['code'] != 0:
                return TuShare.be_output(response['msg'])
            df = pd.DataFrame(response['data']['items'])
            df.columns = response['data']['fields']
            if self.check_if_canceled("TuShare processing"):
                return
            tus_res.append({"content": (df[df['content'].str.contains(self._param.keyword, case=False)]).to_markdown()})
        except Exception as e:
            if self.check_if_canceled("TuShare processing"):
                return
            return TuShare.be_output("**ERROR**: " + str(e))

        if not tus_res:
            return TuShare.be_output("")

        return pd.DataFrame(tus_res)