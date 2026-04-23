def _download_pdf(self, pdf_url):
        """下载PDF文件并验证其完整性"""
        try:
            # 尝试不同的下载方式
            download_methods = [
                # 方法1：直接下载
                lambda: requests.get(pdf_url, proxies=self.proxies, timeout=self.timeout),
                # 方法2：添加 Referer 头
                lambda: requests.get(pdf_url, proxies=self.proxies, timeout=self.timeout,
                                   headers={**self.headers, 'Referer': self.url}),
                # 方法3：使用原始域名作为 Referer
                lambda: requests.get(pdf_url, proxies=self.proxies, timeout=self.timeout,
                                   headers={**self.headers, 'Referer': pdf_url.split('/downloads')[0] if '/downloads' in pdf_url else self.url})
            ]

            for i, download_method in enumerate(download_methods):
                try:
                    logger.info(f"尝试下载方式 {i+1}/3...")
                    response = download_method()
                    if response.status_code == 200:
                        content = response.content
                        if len(content) > 1000 and self._check_pdf_validity(content):  # 确保文件不是太小
                            logger.info(f"PDF下载成功，文件大小: {len(content)} bytes")
                            return content
                        else:
                            logger.warning("下载的文件可能不是有效的PDF")
                    elif response.status_code == 403:
                        logger.warning(f"访问被拒绝 (403 Forbidden)，尝试其他下载方式")
                        continue
                    else:
                        logger.warning(f"下载失败，状态码: {response.status_code}")
                        continue
                except Exception as e:
                    logger.warning(f"下载方式 {i+1} 失败: {str(e)}")
                    continue

            # 如果所有方法都失败，尝试构造替代URL
            try:
                logger.info("尝试使用替代镜像下载...")
                # 从原始URL提取关键信息
                if '/downloads/' in pdf_url:
                    file_part = pdf_url.split('/downloads/')[-1]
                    alternative_mirrors = [
                        f"https://sci-hub.se/downloads/{file_part}",
                        f"https://sci-hub.st/downloads/{file_part}",
                        f"https://sci-hub.ru/downloads/{file_part}",
                        f"https://sci-hub.wf/downloads/{file_part}",
                        f"https://sci-hub.ee/downloads/{file_part}",
                        f"https://sci-hub.ren/downloads/{file_part}",
                        f"https://sci-hub.tf/downloads/{file_part}"
                    ]

                    for alt_url in alternative_mirrors:
                        try:
                            response = requests.get(
                                alt_url,
                                proxies=self.proxies,
                                timeout=self.timeout,
                                headers={**self.headers, 'Referer': alt_url.split('/downloads')[0]}
                            )
                            if response.status_code == 200:
                                content = response.content
                                if len(content) > 1000 and self._check_pdf_validity(content):
                                    logger.info(f"使用替代镜像成功下载: {alt_url}")
                                    return content
                        except Exception as e:
                            logger.debug(f"替代镜像 {alt_url} 下载失败: {str(e)}")
                            continue

            except Exception as e:
                logger.error(f"所有下载方式都失败: {str(e)}")

            return None

        except Exception as e:
            logger.error(f"下载PDF文件失败: {str(e)}")
            return None