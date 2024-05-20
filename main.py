import traceback
from ftplib import FTP
import requests

try:
    import user_config as config
except ImportError:
    import config
import asyncio
from bs4 import BeautifulSoup
from utils import (
    getChannelItems,
    updateChannelUrlsTxt,
    updateFile,
    compareSpeedAndResolution,
    getTotalUrls,
    filter_CCTV_key,
    get_zubao_source_ip,
    find_matching_values, kaisu_upload
)
import logging
import os
from tqdm import tqdm
from urllib.parse import quote, urlencode

# logging.basicConfig(
#     filename="result_new.log",
#     filemode="a",
#     format="%(message)s",
#     level=logging.INFO,
#     encoding='utf-8'
# )
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("result_new.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

headers = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    # 设置请求头中的Content-Type为JSON格式
    'User-Agent': 'Mozilla5.0 (Linux; Android 8.0.0; SM-G955U BuildR16NW) AppleWebKit537.36 (KHTML, like Gecko) Chrome116.0.0.0 Mobile Safari537.36',
    'Host': 'tonkiang.us',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Ch-Ua-Platform': 'Android',
    'Sec-Ch-Ua-Mobile': '1',
    'Sec-Ch-Ua': 'Not_A Brand;v=8, Chromium;v=120, Google Chrome;v=120',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '1',
    'Upgrade-Insecure-Requests': '1',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

post_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
}


class UpdateSource:

    def __init__(self, callback=None):
        self.callback = callback

    async def visitPage(self, channelItems):
        total_channels = sum(len(channelObj) for _, channelObj in channelItems.items())
        pbar = tqdm(total=total_channels)

        subscribe_dict = {}
        search_keyword_list = []
        for area, subscribe_url in config.search_dict.items():
            if subscribe_url.startswith("http:"):
                subscribe_response = requests.get(subscribe_url.strip(), verify=False)
            else:
                subscribe_response = requests.get(subscribe_url.strip())
            subscribe_response.encoding = 'utf-8'
            if subscribe_response.status_code != 200:
                continue
            subscribe_data = subscribe_response.text.split('\n')  # 按行分割数据

            search_area = None
            for line in subscribe_data:
                parts = line.split(',')  # 按逗号分割每一行
                if len(parts) == 2:
                    if parts[1].strip() == "#genre#":
                        search_area = parts[0].strip() if parts[0].strip().startswith(area) else area + parts[0].strip()
                        search_keyword_list.append(search_area)
                        continue
                    key = filter_CCTV_key(parts[0].strip())
                    value = parts[1].strip()
                    if f"{search_area}|{key}" in subscribe_dict:
                        subscribe_dict[f"{search_area}|{key}"].append(value)
                    else:
                        subscribe_dict[f"{search_area}|{key}"] = [value]

        kw_zbip_dict = {}
        for search_kw in search_keyword_list:
            zubo_source_ips = set()
            total_page_size = None
            get_code = None
            session = requests.Session()
            post_form = {
                'saerch': search_kw,
            }
            for page in range(1, config.search_page_num + 1):
                try:
                    if page == 1:
                        response = session.post("http://tonkiang.us/hoteliptv.php", headers=post_headers,
                                                data=post_form)
                    else:
                        page_url = f"http://tonkiang.us/hoteliptv.php?page={page}&pv={quote(search_kw)}&code={get_code}"
                        response = session.get(page_url)
                    response.encoding = "UTF-8"
                    soup = BeautifulSoup(response.text, "html.parser")
                    # tables_div = soup.find("div", class_="tables")
                    results = (
                        soup.find_all("div", class_="result")
                        if soup
                        else []
                    )
                    for result in results:
                        try:
                            zubo_source_ip = get_zubao_source_ip(result)
                            if zubo_source_ip is not None:
                                zubo_source_ips.add(zubo_source_ip)
                        except Exception as e:
                            print(f"Error on result {result}: {e}")
                            continue

                    if total_page_size is None:
                        a_tags = soup.find_all("a")
                        for a_tag in a_tags:
                            href_value = a_tag.get("href")
                            if href_value is not None and href_value.startswith("?page="):
                                val = href_value.replace("?page=", "")
                                page_num = int(val.split("&")[0])
                                if total_page_size is None:
                                    total_page_size = page_num
                                elif page_num > total_page_size:
                                    total_page_size = page_num
                            if get_code is None and href_value is not None and "code=" in href_value:
                                get_code = href_value.split("code=")[1]
                    if total_page_size is None or page >= total_page_size:
                        break
                except Exception as e:
                    # traceback.print_exc()
                    print(f"Error on page {page}: {e}")
                    continue

            if len(zubo_source_ips) == 0:
                continue

            kw_zbip_dict[search_kw] = zubo_source_ips

        for cate, channelObj in channelItems.items():
            channelUrls = {}
            channelObjKeys = channelObj.keys()
            for name in channelObjKeys:
                pbar.set_description(
                    f"Processing {name}, {total_channels - pbar.n} channels remaining"
                )

                infoList = []
                for search_keyword in search_keyword_list:
                    sub_ips = find_matching_values(subscribe_dict, f"{search_keyword}|{filter_CCTV_key(name)}")
                    # sub_ips = subscribe_dict.get(f"{search_keyword}|{filter_CCTV_key(name)}", None)
                    if not sub_ips:
                        continue
                    kw_zbip_list = kw_zbip_dict.get(search_keyword, None)
                    if not kw_zbip_list:
                        continue
                    for zb_ip in kw_zbip_list:
                        for sub_ip in sub_ips:
                            if not sub_ip.startswith("rtp://"):
                                continue
                            rtp_url = sub_ip.replace("rtp:/", f"http://{zb_ip}/rtp")
                            if "#" in rtp_url:
                                urls = rtp_url.split("#")
                                infoList.append([urls[0], None, None])
                                infoList.append([urls[1], None, None])
                            else:
                                infoList.append([rtp_url, None, None])
                try:
                    print(f"[{name}]有{len(infoList)}个直播源进行检测...")
                    sorted_data = await compareSpeedAndResolution(infoList)
                    if sorted_data:
                        channelUrls[name] = (
                                getTotalUrls(sorted_data) or channelObj[name]
                        )
                        for (url, date, resolution), response_time in sorted_data:
                            logger.info(
                                f"Name: {name}, URL: {url}, Date: {date}, Resolution: {resolution}, Response Time: {response_time}fps"
                            )
                except Exception as e:
                    print(f"Error on sorting: {e}")
                    continue
                finally:
                    pbar.update()
            updateChannelUrlsTxt(cate, channelUrls)
            # await asyncio.sleep(1)
        pbar.close()

    def main(self):
        asyncio.run(self.visitPage(getChannelItems()))
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        user_final_file = getattr(config, "final_file", "result.txt")
        user_log_file = (
            "user_result.log" if os.path.exists("user_config.py") else "result.log"
        )
        updateFile(user_final_file, "result_new.txt")
        updateFile(user_log_file, "result_new.log")
        print(f"Update completed! Please check the {user_final_file} file!")

        ftp = None
        try:
            ftp_host = getattr(config, "ftp_host", None)
            ftp_host = ftp_host if ftp_host else os.getenv('ftp_host')
            ftp_port = getattr(config, "ftp_port", None)
            ftp_port = ftp_port if ftp_port else os.getenv('ftp_port')
            ftp_user = getattr(config, "ftp_user", None)
            ftp_user = ftp_user if ftp_user else os.getenv('ftp_user')
            ftp_pass = getattr(config, "ftp_pass", None)
            ftp_pass = ftp_pass if ftp_pass else os.getenv('ftp_pass')
            ftp_remote_file = getattr(config, "ftp_remote_file", None)
            ftp_remote_file = ftp_remote_file if ftp_remote_file else os.getenv('ftp_remote_file')

            if ftp_host and ftp_port and ftp_user and ftp_pass and ftp_remote_file:
                ftp = FTP()
                ftp.connect(ftp_host, int(ftp_port))
                ftp.login(user=ftp_user, passwd=ftp_pass)
                with open(user_final_file, 'rb') as file:
                    up_res = ftp.storbinary(f'STOR {ftp_remote_file}', file)
                    if up_res.startswith('226 Transfer complete'):
                        print('result upload success！')
                    else:
                        print('result upload fail!')

            ks_token = getattr(config, "ks_token", None)
            ks_token = ks_token if ks_token else os.getenv('ks_token')
            ks_file_id = getattr(config, "ks_file_id", None)
            ks_file_id = ks_file_id if ks_file_id else os.getenv('ks_file_id')
            ks_file_name = getattr(config, "ks_file_name", None)
            ks_file_name = ks_file_name if ks_file_name else os.getenv('ks_file_name')
            if ks_token and ks_file_id:
                kaisu_upload(ks_token, user_final_file, ks_file_name, ks_file_id)
        finally:
            if ftp is not None:
                ftp.quit()


if __name__ == '__main__':
    UpdateSource().main()
