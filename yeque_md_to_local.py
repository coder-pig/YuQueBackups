# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : yeque_md_to_local.py
   Author   : CoderPig
   date     : 2023-10-25 19:57
   Desc     : 语雀md文件本地化
-------------------------------------------------
"""
import os
import re
import time
from functools import partial

import aiofiles
from aiohttp_requests import requests

backups_base_dir = os.path.join(os.getcwd(), "backups")
backups_origin_md_dir = os.path.join(backups_base_dir, "origin_md")
backups_local_md_dir = os.path.join(backups_base_dir, "local_md")  # 生成的本地md文件
default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/85.0.4183.121 Safari/537.36 ',
}
pic_match_pattern = re.compile(r'(!\[.*?\]\()(.*?)(\.(png|PNG|jpg|JPG|jepg|gif|GIF|svg|SVG|webp|awebp))(.*?)\)', re.M)
pic_url_path_record_list = []
order_set = {i for i in range(1, 500000)}  # 避免图片名重复后缀


# 递归遍历文夹与子文件夹中的特定后缀文件
def search_all_file(file_dir=backups_origin_md_dir, target_suffix_tuple=('.md')):
    file_list = []
    # 切换到目录下
    os.chdir(file_dir)
    file_name_list = os.listdir(os.curdir)
    for file_name in file_name_list:
        # 获取文件绝对路径
        file_path = "{}{}{}".format(os.getcwd(), os.path.sep, file_name)
        # 判断是否为目录，是往下递归
        if os.path.isdir(file_path):
            file_list.extend(search_all_file(file_path, target_suffix_tuple))
            os.chdir(os.pardir)
        elif target_suffix_tuple is not None and file_name.endswith(target_suffix_tuple):
            file_list.append(file_path)
        else:
            pass
    return file_list


# 异步下载图片
async def download_pic(pic_path, url, headers=None):
    try:
        if headers is None:
            headers = default_headers
        if url.startswith("http") | url.startswith("https"):
            if os.path.exists(pic_path):
                print("图片已存在，跳过下载：%s" % pic_path)
            else:
                resp = await requests.get(url, headers=headers)
                print("下载图片：%s" % url)
                if resp is not None:
                    if resp.status != 404:
                        async with aiofiles.open(pic_path, "wb+") as f:
                            await f.write(await resp.read())
                            print("图片下载完毕：%s" % pic_path)
                    else:
                        print("图片不存在：{}".format(url))
        else:
            print("图片链接格式不正确：%s - %s" % (pic_path, url))
    except Exception as e:
        print("下载异常：{}\n{}".format(url, e))


# 以文本形式读取文件
def read_file_text_content(file_path):
    if not os.path.exists(file_path):
        return None
    else:
        with open(file_path, 'r+', encoding='utf-8') as f:
            return f.read()


# 把文本写入到文件中
def write_text_to_file(content, file_path, mode="w+"):
    try:
        print("文件保存成功：{}".format(file_path))
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content + "\n", )
    except OSError as reason:
        print(str(reason))


# 判断目录是否存在，不存在新建
def is_dir_existed(file_path, mkdir=True):
    if mkdir:
        if not os.path.exists(file_path):
            os.makedirs(file_path)
    else:
        return os.path.exists(file_path)


# 远程图片转换为本地图片
def pic_to_local(match_result, pic_save_dir):
    global pic_url_path_record_list
    pic_url = match_result[2] + match_result[3] + match_result[5]
    print("替换前的图片路径：{}".format(pic_url))
    # 生成新的图片名
    img_file_name = "{}_{}.{}".format(int(round(time.time())), order_set.pop(), match_result[4])
    # 拼接图片相对路径(Markdown用到的)
    relative_path = 'images/{}'.format(img_file_name)
    # 拼接图片绝对路径，下载到本地
    absolute_path = os.path.join(pic_save_dir, img_file_name)
    print("替换后的图片路径：{}".format(relative_path))
    pic_url_path_record_list.append("{}\t{}".format(pic_url, absolute_path))
    # 拼接前后括号()
    return "{}{}{}".format(match_result[1], relative_path, ")")


# md文件本地化
def md_to_local(md_file_list):
    # 遍历backups/origin_md目录下所有md文件
    for md_file_path in md_file_list:
        # 读取md文件内容
        old_content = read_file_text_content(md_file_path)
        # 定位oring_md所在的下标，拼接新生成的md文件的目录要用到
        absolute_dir_index = md_file_path.find("origin_md")
        # 新md文件的相对路径
        md_relative_path = md_file_path[absolute_dir_index + 10:]
        # 新md文件所在目录
        new_md_dir = os.path.join(backups_local_md_dir, md_relative_path[:-3])
        # 新md文件的完整路径
        new_md_file_path = os.path.join(new_md_dir, os.path.basename(md_file_path))
        # 图片的保存路径
        new_picture_dir = os.path.join(new_md_dir, "images")
        # 路径不存在新建
        is_dir_existed(new_md_dir)
        is_dir_existed(new_picture_dir)
        # 替换后的md文件内容
        new_content = pic_match_pattern.sub(partial(pic_to_local, pic_save_dir=new_picture_dir), old_content)
        # 生成新的md文件
        write_text_to_file(new_content, new_md_file_path)
        print("新md文件已生成 → {}".format(new_md_file_path))
    print("所有本地md文件生成完毕！开始批量下载图片文件")

