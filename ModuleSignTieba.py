import re
import requests
import http.cookiejar
import time
import hashlib
import random
import urllib
import datetime
import ConstantQuantity as cq
import ModuleSQL
import ModuleEmail

TimeNow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
DateToday = TimeNow.strftime("%Y-%m-%d")
LogPath = "log/" + DateToday + 'sign'
NumOfSuccess = 0
ListOfTiebaFailToSign = ""
session = requests.Session()

# POST请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (SymbianOS/9.3; Series60/3.2 NokiaE72-1/021.021; Profile/MIDP-2.1 Configuration/CLDC-1.1 )',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}


def CreateLogFile():
    with open(LogPath, 'a+') as f:
        f.close()


def WriteLog(content, IsLineFeed):
    with open(LogPath, 'a+') as f:
        print(content)
        if IsLineFeed == cq.WITH_LINE_FEED:
            f.write(content + "\n")
        elif IsLineFeed == cq.WITHOUT_LINE_FEED:
            f.write(content)
        f.close()


def IsLogin():
    # 验证是否登陆
    url = "https://tieba.baidu.com"
    content = session.get(url, headers=headers).text
    loc = content.find("我爱逛的贴吧")
    if loc > 0:
        return True
    else:
        return False


def FetchTiebaListAndSign():
    # 获取贴吧列表
    url = "http://tieba.baidu.com/mo/m?tn=bdFBW&tab=favorite"
    content = session.get(url, headers=headers, allow_redirects=False).text
    a = r'kw=(.+?)">(.+?)</a></td>'
    a = re.compile(a)
    result = re.findall(a, content)

    # 判断是否已签到
    BDUSS = ""
    for i in session.cookies:
        if i.name == 'BDUSS':
            BDUSS = i.value
    for i in range(0, len(result)):
        WriteLog(u"{0} / {1}...".format((i + 1), len(result)), cq.WITHOUT_LINE_FEED)
        IsSign(result[i][1], BDUSS)


def FetchTiebaInfo(tieba):
    # 获取是否签到以及两个POST用信息
    url = "http://tieba.baidu.com/mo/m?kw=" + tieba
    content = session.get(url, headers=headers, allow_redirects=False).text

    if not content:
        return False

    re_already_sign = '<td style="text-align:right;"><span[ ]>(.*?)<\/span><\/td><\/tr>'
    already_sign = re.findall(re_already_sign, content)

    re_fid = '<input type="hidden" name="fid" value="(.+?)"\/>'
    _fid = re.findall(re_fid, content)
    fid = _fid and _fid[0] or None

    re_tbs = '<input type="hidden" name="tbs" value="(.+?)"\/>'
    _tbs = re.findall(re_tbs, content)
    tbs = _tbs and _tbs[0] or None

    return already_sign, fid, tbs


def EncodeURIPost(postData):
    # 构建POST数据
    SignKey = "tiebaclient!!!"
    s = ""
    keys = postData.keys()
    keys = sorted(keys)
    for i in keys:
        s += i + '=' + postData[i]
    sign = hashlib.md5((s + SignKey).encode("utf8")).hexdigest().upper()
    postData.update({"sign": str(sign)})
    return postData


def IsSign(tieba, BDUSS):
    # 判断是否签到，若未签到则进行签到
    global ListOfTiebaFailToSign
    already_sign, fid, tbs = FetchTiebaInfo(tieba)
    if not already_sign:
        if not fid or not tbs:
            WriteLog(tieba + u"吧......贴吧状态异常，无法签到", cq.WITH_LINE_FEED)
            ListOfTiebaFailToSign += tieba + "  "
            time.sleep(random.uniform(0.5, 1.5))
        else:
            WriteLog(tieba + u"吧......正在尝试签到", cq.WITHOUT_LINE_FEED)
            ExecuteSign(tieba, fid, tbs, BDUSS)
            time.sleep(random.uniform(0.5, 1.5))
    else:
        if already_sign[0] == "已签到":
            WriteLog(tieba + u"吧......已签到", cq.WITH_LINE_FEED)
            time.sleep(random.uniform(0.5, 1.5))
            return


def ExecuteSign(tieba, fid, tbs, BDUSS):
    # 对未签到的贴吧进行签到操作
    global ListOfTiebaFailToSign
    url = "http://c.tieba.baidu.com/c/c/forum/sign"
    data = {
        "BDUSS": BDUSS,
        "_client_id": "03-00-DA-59-05-00-72-96-06-00-01-00-04-00-4C-43-01-00-34-F4-02-00-BC-25-09-00-4E-36",
        "_client_type": "4",
        "_client_version": "1.2.1.17",
        "_phone_imei": "540b43b59d21b7a4824e1fd31b08e9a6",
        "fid": fid,
        'kw': tieba,
        "net_type": "3",
        'tbs': tbs
    }
    data = EncodeURIPost(data)
    data = urllib.parse.urlencode(data)

    try:
        result = session.post(url, data=data).text
        HandelResponse(result)
    except Exception as err:
        WriteLog("......出现异常，签到失败", cq.WITH_LINE_FEED)
        ListOfTiebaFailToSign += tieba + "  "
        WriteLog(err, cq.WITH_LINE_FEED)


def HandelResponse(content):
    global NumOfSuccess
    error_code = re.compile('"error_code":"(\d*?)"').findall(str(content))
    if len(error_code) > 0:
        if error_code[0] == "0":
            WriteLog("......签到成功", cq.WITH_LINE_FEED)
            NumOfSuccess += 1
        elif error_code[0] == "160002":
            WriteLog("......已签到", cq.WITH_LINE_FEED)
        else:
            WriteLog("......签到失败，错误代码为{0}".format(error_code), cq.WITH_LINE_FEED)
    else:
        print(content)


def SingleUserLoginAndSign(username):
    global NumOfSuccess, ListOfTiebaFailToSign
    NumOfSuccess = 0
    ListOfTiebaFailToSign = ""
    TempTimeNow = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    WriteLog("\n" + "[" + TempTimeNow.strftime("%Y-%m-%d %H:%M:%S") + "]  开始为" + username + "签到", cq.WITH_LINE_FEED)
    session.cookies = http.cookiejar.LWPCookieJar("user/" + username)
    try:
        session.cookies.load(ignore_discard=True)
    except IOError:
        WriteLog("Cookie无法加载", cq.WITH_LINE_FEED)
        return False

    if IsLogin():
        WriteLog("成功登陆", cq.WITH_LINE_FEED)
        # 更新COOKIE
        session.cookies.save(ignore_discard=True, ignore_expires=True)
        # 获取贴吧列表并签到
        FetchTiebaListAndSign()
        if len(ListOfTiebaFailToSign) > 0:
            WriteLog("签到完成...{0}个吧签到成功，以下贴吧签到失败".format(NumOfSuccess), cq.WITH_LINE_FEED)
            WriteLog(ListOfTiebaFailToSign, cq.WITH_LINE_FEED)
            EmailContext = "签到完成...{0}个吧签到成功，以下贴吧签到失败".format(NumOfSuccess) + "\n" + ListOfTiebaFailToSign
        else:
            WriteLog("签到完成...{0}个吧签到成功".format(NumOfSuccess), cq.WITH_LINE_FEED)
            EmailContext = "签到完成...{0}个吧签到成功".format(NumOfSuccess)

        IsEmail = ModuleSQL.ExecuteSQL("SELECT IsEmail FROM USERLIST WHERE USERNAME = '{0}'".format(username))[0][0]
        if IsEmail:
            EmailAddress = ModuleSQL.ExecuteSQL("SELECT Email FROM USERLIST WHERE USERNAME = '{0}'".format(username))[0][0]
            ModuleEmail.send_email(EmailAddress, EmailContext)

        return True
    else:
        WriteLog("无法登陆该账号", cq.WITH_LINE_FEED)
        return False


def SignAllUser():
    CreateLogFile()
    SUM = 0
    username = ModuleSQL.ExecuteSQL("SELECT USERNAME FROM USERLIST")
    for i in range(0, len(username)):
        result = ModuleSQL.ExecuteSQL("SELECT IsSign FROM USERLIST WHERE USERNAME = '{0}'".format(username[i][0]))
        if result[0][0] == 1:
            if SingleUserLoginAndSign(username[i][0]):
                SUM += 1

    WriteLog("成功签到{0} / {1}个用户".format(SUM, len(username)), cq.WITH_LINE_FEED)


SignAllUser()
