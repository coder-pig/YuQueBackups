# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : app.py
   Author   : CoderPig
   date     : 2023-10-26 14:57
   Desc     : 语雀备份脚本-入口
-------------------------------------------------
"""
from yuque_doc_backups import init_token, fetch_user_id, fetch_repo_list, fetch_toc_list, doc_count
from yeque_md_to_local import search_all_file, md_to_local, pic_url_path_record_list, download_pic
import asyncio
import time

if __name__ == '__main__':
    yq_token = input("请输入你的语雀Token：")
    if len(yq_token) == 0:
        exit("请输入正确的Token！")
    init_token(yq_token)
    start_time = time.time()
    yq_user_id = fetch_user_id()
    print("开始执行文档备份，请稍等...")
    yq_repo_list = fetch_repo_list(yq_user_id)
    for yq_repo in yq_repo_list:
        print("开始拉取【{}】仓库下的文档".format(yq_repo.repo_name))
        fetch_toc_list(yq_repo.repo_id, yq_repo.repo_name)
    print("文档备份完毕，共记备份文档【{}】篇，开始执行Markdown文件批量本地化...".format(doc_count))
    yq_doc_file_list = search_all_file()
    print("共扫描到Markdown文件【{}】篇，开始批量本地化...".format(len(yq_doc_file_list)))
    md_to_local(yq_doc_file_list)
    loop = asyncio.get_event_loop()
    for pic_url_path_record in pic_url_path_record_list:
        split_list = pic_url_path_record.split("\t")
        loop.run_until_complete(download_pic(split_list[1], split_list[0]))
    print("语雀文档备份及Markdown本地化已执行完毕，共计耗时：{:.2f}ms, 快去打开文件看看吧😄~".format(
        (time.time() - start_time) * 1000))
