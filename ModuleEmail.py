import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import platform
import Privacy


def send_email(receiver, context):
    time_now = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    date_today = time_now.strftime('%Y-%m-%d')
    if platform.system() == "Windows":
        sender = Privacy.EmailSenderWindows
        smtpserver = 'smtp.163.com'
        port = 994
        password = Privacy.EmailPasswordWindows
        print("win")
    else:
        sender = Privacy.EmailSenderCentOS
        smtpserver = 'smtp.gmail.com'
        port = 587
        password = Privacy.EmailPasswordCentOS
    username = sender
    subject = date_today + '贴吧签到情况'

    try:
        # file = open("log\\" + date_today, "r")
        # msg = MIMEText(file.read(), 'plain', 'utf-8')
        msg = MIMEText(context, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'gbk')
        msg['From'] = sender
        msg['To'] = receiver

        smtp = smtplib.SMTP(smtpserver, port=port)
        smtp.set_debuglevel(1)
        # smtp.connect()
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
        print("发送成功")
    except Exception as err:
        print("发送失败")
        print(err)





