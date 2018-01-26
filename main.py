import re
import requests
import http.cookiejar
from PIL import Image
import time
import hashlib
import random
import urllib

sum_success = 0
fail_to_sign = ""

session = requests.Session()
session.cookies = http.cookiejar.LWPCookieJar("cookie")

# POST请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (SymbianOS/9.3; Series60/3.2 NokiaE72-1/021.021; Profile/MIDP-2.1 Configuration/CLDC-1.1 )',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}
#登录时POST请求头
headers_login = {
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding":"gzip,deflate,sdch",
    "Accept-Language":"en-US,en;q=0.8,zh;q=0.6",
    "Host":"passport.baidu.com",
    "Upgrade-Insecure-Requests":"1",
    "Origin":"http://www.baidu.com",
    "Referer":"http://www.baidu.com/",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
}

def fetch_cookies_and_bduss():
    #账号密码
    # user = input("请输入用户名：")
    # password = input("请输入密码：")
    user = ""
    password = ""
    #登陆POST用信息
    token = ""
    verifycode = ""
    codestring = ""
    #第一次POST的信息，如果需要验证码则获取验证码并进行第二次POST
    login_data_first_time = {
        "staticpage": "https://passport.baidu.com/static/passpc-account/html/V3Jump.html",
        "token": token,
        "tpl": "mn",
        "username": user,
        "password": password,
        "loginmerge": "true",
        "mem_pass": "on",
        "logintype": "dialogLogin",
        "logLoginType": "pc_loginDialog",
    }
    #第二次POST的信息
    login_data_second_time = {
        "staticpage": "https://passport.baidu.com/static/passpc-account/html/V3Jump.html",
        "codestring": codestring,
        "verifycode": verifycode,
        "token": token,
        "tpl": "mn",
        "username": user,
        "password": password,
        "loginmerge": "true",
        "mem_pass": "on",
        "logintype": "dialogLogin",
        "logLoginType": "pc_loginDialog",
    }

    print("正在进行登录操作")
    #访问百度主页和登陆页面获取COOKIES
    while(1):
        content = session.get("https://www.baidu.com/").text
        time.sleep(random.uniform(0.5, 1))
        content = session.get("https://passport.baidu.com/v2/api/?login").text
        time.sleep(random.uniform(0.5, 1))
        
        # 获取token信息
        try:
            content = session.get("https://passport.baidu.com/v2/api/?getapi&class=login&tpl=mn&tangram=true", headers=headers).text
            token = re.compile("login_token=\'(\w+?)\';").findall(str(content))[0]
            login_data_first_time["token"] = token
            login_data_second_time["token"] = token
        except:
            print("无法获取token，正在退出...")
            return False

        # 进行第一次登陆POST
        request = session.post("https://passport.baidu.com/v2/api/?login", headers=headers_login, data=login_data_first_time)
        time.sleep(random.uniform(0.5, 1))
        # print(request.text)
        is_captcha = re.compile('error=(\w+?)&').findall(str(request.text))[0]
        if is_captcha == "0":
            # 提取并验证BDUSS
            BDUSS = ""
            for i in session.cookies:
                if i.name == 'BDUSS':
                    BDUSS = i.value
            if BDUSS:
                print("登录成功!")
                return True
            else:
                print("这是个BUG")
                return False
        elif is_captcha == "4" or is_captcha == "7":
            print("密码错误")
            login_data_first_time["password"] = input("请重新输入密码：")
            session.cookies.clear()
            continue
        elif is_captcha == "5" or is_captcha == "120019":
            print("账号异常，请手动登录www.baidu.com验证手机号")
            exit()
        elif is_captcha == "257":
            # 获取验证码地址并写入第二次POST信息
            codestring = re.compile('codestring=(.+?)&username').findall(str(request.text))[0]
            login_data_second_time["codestring"] = codestring
            # 访问验证码地址并下载图片
            request = session.get("https://passport.baidu.com/cgi-bin/genimage?" + codestring, headers=headers)
            with open('captcha.gif', 'wb') as f:
                f.write(request.content)
            img = Image.open('captcha.gif')
            img.show()
            verifycode = input("请填写验证码：")
            # 将验证码内容写入第二次POST信息
            login_data_second_time["verifycode"] = verifycode
            # 进行第二次登陆POST
            request = session.post("https://passport.baidu.com/v2/api/?login", headers=headers_login, data=login_data_second_time)
            is_captcha2 = re.compile('error=(\w+?)&').findall(str(request.text))[0]
            if is_captcha2 == "0":
                # 提取并验证BDUSS
                BDUSS = ""
                for i in session.cookies:
                    if i.name == 'BDUSS':
                        BDUSS = i.value
                if BDUSS:
                    print("登录成功！")
                    return True
                else:
                    print("这是个BUG")
                    return False
            elif is_captcha2 == "6":
                print("验证码错误！")
                session.cookies.clear()
                continue
            elif is_captcha2 == "4" or is_captcha2 == "7":
                print("密码错误")
                password = input("请重新输入密码：")
                login_data_first_time["password"] = password
                login_data_second_time["password"] = password
                session.cookies.clear()
                continue
            else:
                print("未知错误2，错误代码为{0}，请联系管理员".format(is_captcha2))
                exit()
        elif is_captcha == "50028":
            print("输入密码错误次数过多，请三小时后再试")
            exit()
        else:
            print("未知错误1，错误代码为{0}，请联系管理员".format(is_captcha))
            exit()
        #保存COOKIES信息
        session.cookies.save(ignore_discard=True, ignore_expires=True)

def is_login():
    # 验证是否登陆
    url = "https://tieba.baidu.com/index.html"
    content = session.get(url, headers=headers).text
    loc = content.find("爱逛的吧")
    if loc > 0:
        return True
    else:
        return False

def fetch_tieba_list():
    # 获取贴吧列表
    url = "http://tieba.baidu.com/mo/m?tn=bdFBW&tab=favorite"
    content = session.get(url, headers=headers, allow_redirects=False).text
    a = r'kw=(.+?)">(.+?)</a></td>'
    a = re.compile(a)
    result = re.findall(a, content)
    print(u"一共有{0}个喜欢的贴吧".format(len(result)))
    # 判断是否已签到
    BDUSS = ""
    for i in session.cookies:
        if i.name == 'BDUSS':
            BDUSS = i.value
    for i in range (0, len(result)):
        print(u"正在签到第{0} / {1}个贴吧".format((i + 1), len(result)))
        is_sign(result[i][1], BDUSS)

def fetch_tieba_info(tieba):
    # 获取是否签到以及两个POST用信息
    url = "http://tieba.baidu.com/mo/m?kw=" + tieba
    content = session.get(url, headers=headers, allow_redirects=False).text

    if not content:
        return
    re_already_sign = '<td style="text-align:right;"><span[ ]>(.*?)<\/span><\/td><\/tr>'
    already_sign = re.findall(re_already_sign, content)

    re_fid = '<input type="hidden" name="fid" value="(.+?)"\/>'
    _fid = re.findall(re_fid, content)
    fid = _fid and _fid[0] or None

    re_tbs = '<input type="hidden" name="tbs" value="(.+?)"\/>'
    _tbs = re.findall(re_tbs, content)
    tbs = _tbs and _tbs[0] or None
    
    return already_sign, fid, tbs

def encode_uri_post(postData):
    #构建POST数据
    SIGN_KEY = "tiebaclient!!!"
    s = ""
    keys = postData.keys()
    keys = sorted(keys)
    for i in keys:
        s += i + '=' + postData[i]
    sign = hashlib.md5((s + SIGN_KEY).encode("utf8")).hexdigest().upper()
    postData.update({"sign": str(sign)})
    return postData

def is_sign(tieba, BDUSS):
    #判断是否签到，若未签到则进行签到
    global fail_to_sign
    already_sign, fid, tbs = fetch_tieba_info(tieba)
    if not already_sign:
        if not fid or not tbs:
            fail_to_sign += tieba + "  "
            print(tieba + u"吧......贴吧状态异常，无法签到")
            time.sleep(random.uniform(0.5, 1))
        else:
            print(tieba + u"吧......正在尝试签到")
            time.sleep(random.uniform(2, 5))
            sign(tieba, fid, tbs, BDUSS)
    else:
        if already_sign[0] == "已签到":
            print(tieba + u"吧......已签到")
            time.sleep(random.uniform(0.5, 1))
            return

def sign(tieba, fid, tbs, BDUSS):
    global fail_to_sign, sum_success
    url = "http://c.tieba.baidu.com/c/c/forum/sign"
    data={
        "BDUSS" : BDUSS,
        "_client_id" : "03-00-DA-59-05-00-72-96-06-00-01-00-04-00-4C-43-01-00-34-F4-02-00-BC-25-09-00-4E-36",
        "_client_type" : "4",
        "_client_version": "1.2.1.17",
        "_phone_imei": "540b43b59d21b7a4824e1fd31b08e9a6",
        "fid": fid,
        'kw' : tieba,
        "net_type": "3",
        'tbs' : tbs
    }
    data = encode_uri_post(data)
    data = urllib.parse.urlencode(data)

    try:
        result = session.post(url, data=data)
        handle_response(result.text, tieba)
    except Exception as err:
        fail_to_sign += tieba + "  "
        print(u"%s吧......签到失败，出现异常" % tieba)
        print(err)

def handle_response(content, tieba):
    global sum_success
    error_code = re.compile('"error_code":"(\d*?)"').findall(str(content))[0]
    if error_code[0] == "0":
        print(u"签到成功")
        sum_success += 1
    elif error_code[0] == "160002":
        print(u"已签到")
    else:
        print(u"签到失败，错误代码为{0}".format(error_code))

if __name__ == "__main__":
    # fp = open("user_list", "w+")
    try:
        session.cookies.load(ignore_discard=True)
    except IOError:
        print(u"Cookies未加载！")
        if fetch_cookies_and_bduss() == False:
            exit()

    if is_login():
        print(u"成功登录")
        #更新COOKIE
        session.cookies.save(ignore_discard=True, ignore_expires=True)
        #获取贴吧列表并签到
        fetch_tieba_list()
        print(u"签到完成 {0}个吧签到成功，以下贴吧签到失败".format(sum_success))
        print(fail_to_sign)
    else:
        print(u"无法登陆该账号")
