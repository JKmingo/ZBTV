source_file = "demo.txt"
final_file = "result.txt"
zb_urls_limit = 3
response_time_weight = 0.5
resolution_weight = 0.5
# 1: 显示默认值，线路1 线路2，2：显示视频分辨率，如:1080x720
xianlu_type = 1
# ffmpeg解析视频时间，单位秒
ffmpeg_time = 10
# key: 地区，在http://tonkiang.us网站上搜索的关键词
# value: 订阅url，在https://github.com/xisohi/IPTV-Multicast-source中找自己想要的
search_dict = {
    "四川": "https://raw.githubusercontent.com/lufly9/Y/main/订阅.txt"
}
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_pass = ""
ftp_remote_file = ""
