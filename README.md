# 使用代理处理反爬抓取微信文章

- 1 抓取索引页面内容

利用requests请求目标站点，得到索引页网页HTML代码，返回结果。

- 2 代理设置

如果遇到302状态码，则证明IP被封，切换代理重试。

- 3 分析详情页内容

请求详情页，分析得到标题，正文等内容。

- 4 将数据保存到数据库

将结构化数据保存到MongoDB