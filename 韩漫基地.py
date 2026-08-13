# -*- coding: utf-8 -*-
# 韓漫基地 TVBox 爬虫 - 带筛选 + 图片提取增强
# 网站: https://hmjd8.com

import sys
import json
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider as BaseSpider

class Spider(BaseSpider):
    def getName(self):
        return "韓漫基地"

    def init(self, extend=""):
        self.baseUrl = "https://hmjd8.com"
        self.session = requests.Session()
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        self.headers = {
            'User-Agent': self.ua,
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': self.baseUrl + '/'
        }
        self.session.headers.update(self.headers)

    def get_header(self, url=None):
        h = self.headers.copy()
        if url:
            h['Referer'] = url
        return h

    def homeContent(self, filter):
        # ---- 主分类（大分类） ----
        classes = [
            {"type_name": "📌 全部漫畫", "type_id": "all"},
            {"type_name": "🆕 最新更新", "type_id": "update"},
            {"type_name": "📖 連載中", "type_id": "serialized"},
            {"type_name": "✅ 已完結", "type_id": "completed"},
            {"type_name": "⭐ 精選推薦", "type_id": "recommend"},
            {"type_name": "🔥 最受歡迎", "type_id": "ranking"},
        ]

        # ---- 为“全部漫畫”提供筛选（题材 + 排序） ----
        subjects = [
            "全部", "正妹", "恋爱", "出版漫画", "肉慾", "浪漫", "大尺度",
            "巨乳", "有夫之婦", "女大生", "狗血劇", "同居", "好友",
            "調教", "动作", "後宮", "不倫", "3D", "校園",
            "耽美", "日漫"
        ]
        filters = {
            "all": [
                {
                    "key": "subject",
                    "name": "题材",
                    "value": [{"n": s, "v": s} for s in subjects]
                },
                {
                    "key": "order",
                    "name": "排序",
                    "value": [
                        {"n": "按時間", "v": "time"},
                        {"n": "按閱讀", "v": "hits"}
                    ]
                }
            ]
        }

        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        # 首页推荐显示“最新更新”
        return self.categoryContent("update", "1", None, {})

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if pg else 1

        # ---- 特殊分类（无筛选） ----
        special_urls = {
            "update": f"{self.baseUrl}/update?page={pg}",
            "ranking": f"{self.baseUrl}/ranking?page={pg}",
            "recommend": f"{self.baseUrl}/update/recommend?page={pg}",
            "serialized": f"{self.baseUrl}/manhua/all/ob/time/st/serialized/page/{pg}",
            "completed": f"{self.baseUrl}/manhua/all/ob/time/st/completed/page/{pg}",
        }

        if tid in special_urls:
            url = special_urls[tid]
        elif tid == "all":
            # 从 extend 中获取筛选参数
            subject = extend.get("subject", "全部") if extend else "全部"
            order = extend.get("order", "time") if extend else "time"
            subject_param = "all" if subject == "全部" else subject
            url = f"{self.baseUrl}/manhua/{subject_param}/ob/{order}/st/all/page/{pg}"
        else:
            # 兜底（一般不会走到这里）
            url = f"{self.baseUrl}/manhua/all/ob/time/st/all/page/{pg}"

        try:
            r = self.session.get(url, headers=self.get_header(url), timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')

            items = soup.select('li.hl-list-item')
            if not items:
                items = soup.select('.hl-list-item')

            videos = []
            for item in items:
                try:
                    thumb = item.select_one('a.hl-item-thumb')
                    if not thumb:
                        continue
                    href = thumb.get('href', '')
                    if not href or 'page-' in href:
                        continue

                    vid_match = re.search(r'/manhua-(\d+)\.html', href)
                    vid = vid_match.group(1) if vid_match else href

                    pic = thumb.get('data-original') or thumb.get('data-src') or thumb.get('src') or ''
                    if pic.startswith('//'):
                        pic = 'https:' + pic

                    title_tag = item.select_one('.hl-item-title a')
                    title = title_tag.get_text(strip=True) if title_tag else '未知'

                    sub_tag = item.select_one('.hl-item-sub')
                    remark = sub_tag.get_text(strip=True) if sub_tag else ''

                    videos.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                except Exception:
                    continue

            return {
                "list": videos,
                "page": pg,
                "pagecount": 9999,
                "limit": len(videos) if len(videos) > 0 else 24,
                "total": 999999
            }
        except Exception as e:
            print(f"categoryContent error: {e}")
            return {"list": [], "page": pg, "pagecount": 1, "limit": 0, "total": 0}

    def searchContent(self, key, quick, pg="1"):
        pg = int(pg) if pg else 1
        key_enc = urllib.parse.quote(key)
        url = f"{self.baseUrl}/catalog.php?key={key_enc}&page={pg}"

        try:
            r = self.session.get(url, headers=self.get_header(url), timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')

            items = soup.select('li.hl-list-item')
            if not items:
                items = soup.select('.hl-list-item')

            videos = []
            for item in items:
                try:
                    thumb = item.select_one('a.hl-item-thumb')
                    if not thumb:
                        continue
                    href = thumb.get('href', '')
                    if not href or 'page-' in href:
                        continue

                    vid_match = re.search(r'/manhua-(\d+)\.html', href)
                    vid = vid_match.group(1) if vid_match else href

                    pic = thumb.get('data-original') or thumb.get('data-src') or thumb.get('src') or ''
                    if pic.startswith('//'):
                        pic = 'https:' + pic

                    title_tag = item.select_one('.hl-item-title a')
                    title = title_tag.get_text(strip=True) if title_tag else '未知'

                    sub_tag = item.select_one('.hl-item-sub')
                    remark = sub_tag.get_text(strip=True) if sub_tag else ''

                    videos.append({
                        "vod_id": vid,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                except Exception:
                    continue

            return {"list": videos, "page": pg, "pagecount": 9999, "limit": len(videos), "total": 999999}
        except Exception as e:
            print(f"searchContent error: {e}")
            return {"list": []}

    def detailContent(self, ids):
        vid = ids[0] if ids else ''
        if not vid:
            return {"list": []}

        url = f"{self.baseUrl}/manhua-{vid}.html"

        try:
            r = self.session.get(url, headers=self.get_header(url), timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')

            title_tag = soup.select_one('h1') or soup.select_one('.hl-dc-title')
            title = title_tag.get_text(strip=True) if title_tag else '未知'

            cover = ''
            cover_tag = soup.select_one('.hl-dc-pic .hl-item-thumb')
            if cover_tag:
                cover = cover_tag.get('data-original') or cover_tag.get('data-src') or cover_tag.get('src') or ''
                if cover.startswith('//'):
                    cover = 'https:' + cover

            desc_tag = soup.select_one('.hl-data-xs .blurb') or soup.select_one('.blurb')
            if desc_tag:
                desc = desc_tag.get_text(strip=True)
            else:
                desc_tag = soup.select_one('.hl-data-xs')
                desc = desc_tag.get_text(strip=True) if desc_tag else ''

            chapter_items = soup.select('.hl-plays-list a')
            if not chapter_items:
                chapter_items = soup.select('.hl-play-source a')
            if not chapter_items:
                chapter_items = soup.select('ul.hl-plays-list a')

            play_list = []
            for a in chapter_items:
                ch_name = a.get_text(strip=True)
                ch_href = a.get('href', '')
                if not ch_href:
                    continue
                if not ch_href.startswith('http'):
                    ch_href = self.baseUrl + ch_href if ch_href.startswith('/') else self.baseUrl + '/' + ch_href
                play_list.append(f"{ch_name}${ch_href}")

            if not play_list:
                play_list.append(f"阅读${url}")

            play_url = "#".join(play_list)

            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": cover,
                    "vod_content": desc,
                    "vod_play_from": "韓漫基地",
                    "vod_play_url": play_url
                }]
            }
        except Exception as e:
            print(f"detailContent error: {e}")
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        url = id
        try:
            r = self.session.get(url, headers=self.get_header(url), timeout=15)
            r.encoding = 'utf-8'
            html = r.text

            # ---------- 多种方式提取图片 ----------
            img_list = []

            # 方式1: 从 #m_r_imgbox_0 中提取所有 data-src
            soup = BeautifulSoup(html, 'html.parser')
            img_box = soup.select_one('#m_r_imgbox_0')
            if img_box:
                imgs = img_box.select('img[data-src]')
                for img in imgs:
                    src = img.get('data-src', '').strip()
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        if not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'banner', 'button', 'ad', 'loading']):
                            img_list.append(src)

            # 方式2: 如果方式1没有或数量少，直接从整个页面提取所有 img 标签的 data-src 和 src
            if len(img_list) < 2:
                all_imgs = soup.select('img[data-src]')
                for img in all_imgs:
                    src = img.get('data-src', '').strip()
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        if not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'banner', 'button', 'ad', 'loading']):
                            if src not in img_list:
                                img_list.append(src)

            # 方式3: 使用正则提取所有图片链接（包括背景图等）
            if len(img_list) < 2:
                # 匹配常见图片扩展名
                pattern = r'((?:https?:|//)[^"\'\s<>]+\.(?:jpg|png|webp|jpeg)(?:\?[^"\'\s]*)?)'
                matches = re.findall(pattern, html, re.I)
                for src in matches:
                    if src.startswith('//'):
                        src = 'https:' + src
                    if not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'banner', 'button', 'ad', 'loading']):
                        if src not in img_list:
                            img_list.append(src)

            # 方式4: 从 CSS 背景图提取（如 background-image: url(...)）
            if len(img_list) < 2:
                bg_pattern = r'background(?:-image)?\s*:\s*url\([\'"]?([^\)\'"]+)[\'"]?\)'
                bg_matches = re.findall(bg_pattern, html, re.I)
                for src in bg_matches:
                    if src.startswith('//'):
                        src = 'https:' + src
                    if not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'banner', 'button', 'ad', 'loading']):
                        if src not in img_list:
                            img_list.append(src)

            # 去重
            img_list = list(dict.fromkeys(img_list))

            if not img_list:
                # 如果还是没有图片，检查页面是否包含视频（可能是视频页）
                if '<video' in html or '.m3u8' in html or '.mp4' in html:
                    # 尝试提取视频链接
                    video_pattern = r'(https?://[^"\'\s<>]+\.(?:m3u8|mp4)[^"\'\s]*)'
                    video_matches = re.findall(video_pattern, html, re.I)
                    if video_matches:
                        return {
                            "parse": 0,
                            "playUrl": "",
                            "url": video_matches[0],
                            "header": json.dumps(self.get_header(url))
                        }
                return {"parse": 0, "url": "", "msg": "未找到图片"}

            # 返回图片列表（使用 pics:// 协议）
            return {
                "parse": 0,
                "playUrl": "",
                "url": "pics://" + "&&".join(img_list),
                "header": json.dumps(self.get_header(url))
            }
        except Exception as e:
            return {"parse": 0, "url": "", "msg": f"Err:{e}"}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        if self.session:
            self.session.close()

    def localProxy(self, param):
        return None