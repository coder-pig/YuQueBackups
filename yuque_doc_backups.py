# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : yuque_doc_backups.py
   Author   : CoderPig
   date     : 2023-10-25 14:30
   Desc     : 语雀文档备份脚本
-------------------------------------------------
"""
import os.path

import requests as r
import time
from random import randint

yq_headers = None
yq_base_url = "https://www.yuque.com/api/v2/{}"
backups_base_dir = os.path.join(os.getcwd(), "backups")
backups_origin_md_dir = os.path.join(backups_base_dir, "origin_md")
doc_count = 0

# 判断目录是否存在，不存在新建
def is_dir_existed(file_path, mkdir=True):
    if mkdir:
        if not os.path.exists(file_path):
            os.makedirs(file_path)
    else:
        return os.path.exists(file_path)


# 把文本写入到文件中
def write_text_to_file(content, file_path, mode="w+"):
    try:
        print("文件保存成功：{}".format(file_path))
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content + "\n", )
    except OSError as reason:
        print(str(reason))


# 扫描特定目录下特定文件后缀，返回文件路径列表
def scan_file_list_by_suffix(file_dir=os.getcwd(), suffix=""):
    return [os.path.join(file_dir, x) for x in os.listdir(file_dir) if x.endswith(suffix)]


# 知识库
class Repo:
    def __init__(self, repo_id, repo_type, repo_slug, repo_name, repo_namespace):
        self.repo_id = repo_id
        self.repo_ype = repo_type
        self.repo_slug = repo_slug
        self.repo_name = repo_name
        self.repo_namespace = repo_namespace


# 目录结点
class TocNode:
    def __init__(self, node_type, node_title, node_uuid, parent_uuid, doc_id, repo_id, repo_name):
        self.node_type = node_type
        self.node_title = node_title
        self.node_uuid = node_uuid
        self.parent_uuid = parent_uuid
        self.child_node_list = []
        self.doc_id = doc_id
        self.repo_id = repo_id
        self.repo_name = repo_name


# 文档
class Doc:
    def __init__(self, doc_id, book_id, book_name, doc_slug, doc_title, doc_content):
        self.doc_id = doc_id
        self.book_id = book_id
        self.book_name = book_name;
        self.doc_slug = doc_slug
        self.doc_title = doc_title
        self.doc_content = doc_content

    def save_to_md(self):
        save_path = "{}{}{}{}{}.md".format(backups_origin_md_dir, os.path.sep, self.book_name, os.path.sep,
                                           self.doc_title)
        print(save_path)


# 初始化Token
def init_token(token):
    global yq_headers
    yq_headers = {'X-Auth-Token': token}
    print("Token初始化成功...\n{}".format('=' * 64))


# 发起请求
def send_request(desc, api):
    request_url = yq_base_url.format(api)
    print("请求{}接口：{}".format(desc, request_url))
    return r.get(request_url, headers=yq_headers)


# 获取用户id
def fetch_user_id():
    # 获取用户ID
    user_resp = send_request("获取用户ID", "user")
    user_id = None
    if user_resp:
        user_id = user_resp.json().get('data').get('id')
        print("当前用户ID：{}".format(user_id))
    if user_id is None:
        exit("用户ID获取失败，请检查后重试...")
    print("=" * 64)
    return user_id


# 拉取知识库列表
def fetch_repo_list(user_id):
    repo_list_resp = send_request("知识库列表", "users/{}/repos".format(user_id))
    repo_list = []
    if repo_list_resp:
        repo_list_json = repo_list_resp.json()
        for repo in repo_list_json['data']:
            repo_list.append(
                Repo(repo.get('id'), repo.get('type'), repo.get('slug'), repo.get('name'), repo.get('namespace')))
    if len(repo_list) == 0:
        exit("知识库列表获取失败，请检查后重试...")
    else:
        print("解析知识库列表成功，共{}个知识库...".format(len(repo_list)))
    print("=" * 64)
    return repo_list


# 拉取知识库目录
def fetch_toc_list(repo_id, repo_name):
    toc_list_resp = send_request("目录列表", "repos/{}/toc".format(repo_id))
    id_order_dict = {}
    root_toc_node = TocNode(None, "根目录", None, None, None, repo_id, repo_name)
    id_order_dict["root"] = root_toc_node
    if toc_list_resp:
        toc_list_json = toc_list_resp.json()
        for toc in toc_list_json['data']:
            toc_node = TocNode(toc.get('type'), toc.get('title'), toc.get('uuid'), toc.get('parent_uuid'),
                               toc.get('doc_id'), repo_id, repo_name)
            id_order_dict[toc_node.node_uuid] = toc_node
            # 顶级目录
            if toc_node.parent_uuid is None or len(toc_node.parent_uuid) == 0:
                root_toc_node.child_node_list.append(toc_node)
            else:
                parent_node = id_order_dict.get(toc_node.parent_uuid)
                if parent_node is None:
                    exit("父目录不存在")
                else:
                    parent_node.child_node_list.append(toc_node)
    for node in root_toc_node.child_node_list:
        traverse_nodes(node)


# 递归访问目录树的测试方法
def traverse_nodes(node, save_path=""):
    # 格式化节点标题
    unformat_node_title = "{}".format(node.node_title)
    format_node_title = unformat_node_title.replace("|", "_").replace("/", "、").replace('"', "'").replace(":", "；")
    # 追加节点标题到当前路径
    save_path += "{}{}".format(os.sep, format_node_title)
    # 生成文件路径
    if node.child_node_list is None or len(node.child_node_list) == 0:
        if node.node_type == "DOC":
            format_repo_name = node.repo_name.replace("|", "_").replace("/", "、").replace('"', "'").replace(":", "；")
            md_save_path = "{}{}{}{}.md".format(backups_origin_md_dir, os.sep, format_repo_name, save_path)
            last_sep_index = md_save_path.rfind(os.sep)
            if last_sep_index != -1:
                save_dir = md_save_path[:last_sep_index]
                is_dir_existed(save_dir)
                fetch_doc_detail(node, md_save_path)
        return
    else:
        for node in node.child_node_list:
            traverse_nodes(node, save_path)


# 拉取单篇文章的详细内容
def fetch_doc_detail(node, save_path):
    global doc_count
    doc_detail_resp = send_request("文档详情", "repos/{}/docs/{}".format(node.repo_id, node.doc_id))
    if doc_detail_resp:
        doc_detail_json = doc_detail_resp.json()
        doc_detail = doc_detail_json.get('data').get('body')
        if doc_detail is not None and len(doc_detail) > 0:
            write_text_to_file(doc_detail, save_path)
            doc_count += 1
            print("第【{}】篇文档备份成功...".format(doc_count))
            time.sleep(randint(2, 8))  # 随机休眠2-8s，细水长流~
    return doc_count
