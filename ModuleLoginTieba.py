import re
import requests
import time
import random
import http.cookiejar
import datetime
import ConstantQuantity as cq

session = requests.Session()
BaiduUsername = ""
BaiduPassword = ""
BaiduURLCaptcha = ""
BaiduToken = ""
BaiduVerifyCode = ""
BaiduCodeString = ""
TimeNow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
DateToday = TimeNow.strftime("%Y-%m-%d")
LogPath = "log/" + DateToday + 'reg'

# POST请求头
CommonHeaders = {
    'User-Agent': 'Mozilla/5.0 (SymbianOS/9.3; Series60/3.2 NokiaE72-1/021.021; Profile/MIDP-2.1 Configuration/CLDC-1.1 )',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}
# 登录时POST请求头
LoginHeaders = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8,zh;q=0.6",
    "Host": "passport.baidu.com",
    "Upgrade-Insecure-Requests": "1",
    "Origin": "http://www.baidu.com",
    "Referer": "http://www.baidu.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
}

# 第一次POST的信息，如果需要验证码则获取验证码并进行第二次POST
DataLoginBaiduFirstTime = {
    "staticpage": "https://passport.baidu.com/static/passpc-account/html/V3Jump.html",
    "token": BaiduToken,
    "tpl": "mn",
    "username": BaiduUsername,
    "password": BaiduPassword,
    "loginmerge": "true",
    "mem_pass": "on",
    "logintype": "dialogLogin",
    "logLoginType": "pc_loginDialog",
}
# 第二次POST的信息
DataLoginBaiduSecondTime = {
    "staticpage": "https://passport.baidu.com/static/passpc-account/html/V3Jump.html",
    "codestring": BaiduCodeString,
    "verifycode": BaiduVerifyCode,
    "token": BaiduToken,
    "tpl": "mn",
    "username": BaiduUsername,
    "password": BaiduPassword,
    "loginmerge": "true",
    "mem_pass": "on",
    "logintype": "dialogLogin",
    "logLoginType": "pc_loginDialog",
}


def WriteLog(content, IsLineFeed):
    with open(LogPath, 'a+') as f:
        print(content)
        if IsLineFeed == cq.WITH_LINE_FEED:
            f.write(content + "\n")
        elif IsLineFeed == cq.WITHOUT_LINE_FEED:
            f.write(content)
        f.close()


def FetchCaptcha(username, password):
    global BaiduURLCaptcha
    DataLoginBaiduFirstTime["username"] = username
    DataLoginBaiduSecondTime["username"] = username
    DataLoginBaiduFirstTime["password"] = password
    DataLoginBaiduSecondTime["password"] = password

    if not FetchToken():
        return False

    # 进行第一次登陆POST
    WriteLog("正在尝试登录", cq.WITH_LINE_FEED)
    request = session.post("https://passport.baidu.com/v2/api/?login", headers=LoginHeaders,
                           data=DataLoginBaiduFirstTime)
    time.sleep(random.uniform(0.2, 0.5))
    # print(request.text)
    state = re.compile('error=(\w+?)&').findall(str(request.text))[0]
    if state == "0":
        # 提取并验证  BDUSS
        BDUSS = ""
        for i in session.cookies:
            if i.name == 'BDUSS':
                BDUSS = i.value
        if BDUSS:
            WriteLog("登录成功!", cq.WITH_LINE_FEED)
            return cq.LOGIN_SUCCESS
        else:
            WriteLog("这是个BUG", cq.WITH_LINE_FEED)
            return cq.ITS_A_BUG
    elif state == "4" or state == "7":
        WriteLog("密码错误", cq.WITH_LINE_FEED)
        session.cookies.clear()
        return cq.WRONG_PASSWORD
    elif state == "5" or state == "120019":
        WriteLog("账号异常，请手动登录www.baidu.com验证手机号", cq.WITH_LINE_FEED)
        return cq.ABNORMAL_STATE
    elif state == "257":
        # 获取验证码
        WriteLog("正在获取验证码", cq.WITH_LINE_FEED)
        CodeString = re.compile('codestring=(.+?)&username').findall(str(request.text))[0]
        DataLoginBaiduSecondTime["codestring"] = CodeString
        BaiduURLCaptcha = "https://passport.baidu.com/cgi-bin/genimage?" + CodeString
        # 访问验证码地址并下载图片
        return cq.NEED_CAPTCHA
    elif state == "50028":
        WriteLog("输入密码错误次数过多，请三小时后再试", cq.WITH_LINE_FEED)
        return cq.EXCESSIVE_WRONG_PASSWORD
    else:
        WriteLog("未知错误1，错误代码为{0}，请联系管理员".format(state), cq.WITH_LINE_FEED)
        return cq.UNEXPECTED_ERROR


def FetchDBUSS(captcha):
    # 将验证码内容写入第二次POST信息
    DataLoginBaiduSecondTime["verifycode"] = captcha
    # 进行第二次登陆POST
    WriteLog("验证验证码", cq.WITH_LINE_FEED)
    request = session.post("https://passport.baidu.com/v2/api/?login", headers=LoginHeaders, data=DataLoginBaiduSecondTime)
    # print(request.text)
    state = re.compile('error=(\w+?)&').findall(str(request.text))[0]
    if state == "0":
        # 提取并验证BDUSS
        BDUSS = ""
        for i in session.cookies:
            if i.name == 'BDUSS':
                BDUSS = i.value
        if BDUSS:
            WriteLog("登录成功!", cq.WITH_LINE_FEED)
            return cq.LOGIN_SUCCESS
        else:
            WriteLog("这是个BUG", cq.WITH_LINE_FEED)
            return cq.ITS_A_BUG
    elif state == "6":
        WriteLog("验证码错误!", cq.WITH_LINE_FEED)
        return cq.WRONG_CAPTCHA
    elif state == "4" or state == "7":
        WriteLog("密码错误", cq.WITH_LINE_FEED)
        return cq.WRONG_PASSWORD
    elif state == "120021":
        WriteLog("账号异常，请手动登录www.baidu.com验证邮箱", cq.WITH_LINE_FEED)
        return cq.ABNORMAL_STATE
    else:
        WriteLog("未知错误2，错误代码为{0}，请联系管理员".format(state), cq.WITH_LINE_FEED)
        return cq.UNEXPECTED_ERROR


def FetchToken():
    WriteLog(u"正在尝试获取Token", cq.WITH_LINE_FEED)
    # 访问百度主页和登陆页面获取COOKIE
    content = session.get("https://www.baidu.com/").text
    time.sleep(random.uniform(0.2, 0.5))
    content = session.get("https://passport.baidu.com/v2/api/?login").text
    time.sleep(random.uniform(0.2, 0.5))

    # 获取token信息
    try:
        content = session.get("https://passport.baidu.com/v2/api/?getapi&class=login&tpl=mn&tangram=true", headers=CommonHeaders).text
        token = re.compile("login_token=\'(\w+?)\';").findall(str(content))[0]
        DataLoginBaiduFirstTime["token"] = token
        DataLoginBaiduSecondTime["token"] = token
        WriteLog("已获取Token", cq.WITH_LINE_FEED)
        return True
    except Exception as err:
        WriteLog("无法获取Token，正在退出...，错误为{0}".format(err), cq.WITH_LINE_FEED)
        return False


def NewUser(username, password):
    global BaiduURLCaptcha, BaiduUsername, BaiduPassword
    BaiduUsername = username
    BaiduPassword = password
    TempTimeNow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    WriteLog("\n" + "[" + TempTimeNow.strftime("%Y-%m-%d %H:%M:%S") + "]  开始为" + BaiduUsername + "注册", cq.WITH_LINE_FEED)
    with open("user/" + BaiduUsername, "a+") as f:
        f.close()
    session.cookies = http.cookiejar.LWPCookieJar("user/" + BaiduUsername)
    state = FetchCaptcha(BaiduUsername, BaiduPassword)
    if state == cq.NEED_CAPTCHA:
        print(BaiduURLCaptcha)
        VerifyCaptcha()
    elif state == cq.LOGIN_SUCCESS:
        session.cookies.save(ignore_discard=True, ignore_expires=True)
        WriteLog("登录成功", cq.WITH_LINE_FEED)
    else:
        WriteLog("Error in NewUser", cq.WITH_LINE_FEED)


def VerifyCaptcha():
    global BaiduURLCaptcha
    captcha = input("captcha:")
    is_login = FetchDBUSS(captcha)
    if is_login == "登录成功！":
        # 保存COOKIE信息
        session.cookies.save(ignore_discard=True, ignore_expires=True)
        print("登录成功！")
    elif is_login == "验证码错误！":
        BaiduURLCaptcha = FetchCaptcha(BaiduUsername, BaiduPassword)
        # print(url_captcha)
        print("验证码错误！")
    elif is_login == "密码错误":
        print("密码错误！")
    else:
        print("Error in VerifyCaptcha")

