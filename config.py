source_file = "demo.txt"
final_file = "result.txt"
zb_urls_limit = 10
response_time_weight = 0.5
resolution_weight = 0.5
# 1: 显示默认值，线路1 线路2，2：显示视频分辨率，如:1080x720
xianlu_type = 2
# ffmpeg解析视频时间，单位秒
ffmpeg_time = 10
# key: 地区，在http://tonkiang.us网站上搜索的关键词
# value: 订阅url，在https://github.com/xisohi/IPTV-Multicast-source中找自己想要的
search_dict = {
    "上海": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/xisohi/IPTV-Multicast-source/main/shanghai/telecom.txt",
    "广东": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/xisohi/IPTV-Multicast-source/main/guangdong/telecom.txt"
}
search_page_num = 10
search_ignore_key = ["高清", "4K"]
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_pass = ""
ftp_remote_file = ""

# 凯速网上传文件配置
ks_token = ""
ks_file_id = "0" #文件目录id，0为根目录
ks_file_name = ""
