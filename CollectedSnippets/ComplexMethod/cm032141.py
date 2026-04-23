def _send_request(self):
        """发送请求到Sci-Hub镜像站点"""
        # 首先测试代理连接
        if self.use_proxy and not self._test_proxy_connection():
            logger.warning("代理连接不可用，切换到直连模式")
            self.use_proxy = False
            self.proxies = None

        last_exception = None
        working_mirrors = []

        # 先测试哪些镜像可用
        logger.info("正在测试镜像站点可用性...")
        for mirror in self.MIRRORS:
            try:
                test_response = requests.get(
                    mirror,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=10
                )
                if test_response.status_code == 200:
                    working_mirrors.append(mirror)
                    logger.info(f"镜像 {mirror} 可用")
                    if len(working_mirrors) >= 5:  # 找到5个可用镜像就够了
                        break
            except Exception as e:
                logger.debug(f"镜像 {mirror} 不可用: {str(e)}")
                continue

        if not working_mirrors:
            raise Exception("没有找到可用的镜像站点")

        logger.info(f"找到 {len(working_mirrors)} 个可用镜像，开始尝试下载...")

        # 使用可用的镜像进行下载
        for mirror in working_mirrors:
            try:
                res = requests.post(
                    mirror,
                    headers=self.headers,
                    data=self.payload,
                    proxies=self.proxies,
                    timeout=self.timeout
                )
                if res.ok:
                    logger.info(f"成功使用镜像站点: {mirror}")
                    self.url = mirror  # 更新当前使用的镜像
                    time.sleep(1)  # 降低等待时间以提高效率
                    return res
            except Exception as e:
                logger.error(f"尝试镜像 {mirror} 失败: {str(e)}")
                last_exception = e
                continue

        if last_exception:
            raise last_exception
        raise Exception("所有可用镜像站点均无法完成下载")