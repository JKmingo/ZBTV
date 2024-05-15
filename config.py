source_file = "demo.txt"
final_file = "result.txt"
zb_urls_limit = 10
response_time_weight = 0.5
resolution_weight = 0.5
# key: 地区，在http://tonkiang.us网站上搜索的关键词
# value: 订阅url，在https://github.com/xisohi/IPTV-Multicast-source中找自己想要的
search_dict = {
    "北京": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/xisohi/IPTV-Multicast-source/main/beijing/beijing.txt",
    "四川": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/xisohi/IPTV-Multicast-source/main/sichuan/telecom.txt",
}
# ftp上传result.txt文件
ftp_host = ""
ftp_port = ""
ftp_user = ""
ftp_pass = ""
ftp_remote_file = ""
