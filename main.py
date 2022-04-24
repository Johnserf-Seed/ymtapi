# -*- coding:utf-8 -*-
from flask import Flask
from flask import request
import time,os,sqlite3,re,json
import requests

# 工厂模式
app = Flask(__name__, instance_relative_config=True)

# 防止中文被转义
app.config['JSON_AS_ASCII'] = False

# 数据库文件
DATABASE = 'info.sqlite'

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# 获取当前时间戳
def now2ticks(type):
    """
    @description  : 获取当前时间戳
    ---------
    @param  : type，返回值类型
    -------
    @Returns  : 1650721580 || '1650721580'
    -------
    """
    if type == 'int':
        return int(round(time.time() * 1000))
    elif type == 'str':
        return str(int(round(time.time() * 1000)))

#检查学号
def checkid(id):
    if re.findall('^\d{11}$', id) == []:
        return '学号错误'
    else:
        return re.findall('^\d{11}$', id)

#首页
@app.route('/')
def index():
    return {'code':200,'result':'/login?id=','timestamp':now2ticks('int')}

#token
@app.route('/login', methods=["GET","POST"])
def login():
    id = request.args.get('id','')

    if id == '' or len(id) != 11:
        return {'code':200,'result':'学号错误','timestamp':now2ticks('int')}

    password = 'xysoft123'
    loginurl = 'http://ymt.zjiet.edu.cn/campuspassng/sys/login'
    userurl = 'http://ymt.zjiet.edu.cn/campuspassng//campuspass/user/user'
    loginheaders = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Connection': 'keep-alive',
        'Content-Length': '49',
        'Content-Type': 'application/json;charset=UTF-8',
        'Host': 'ymt.zjiet.edu.cn',
        'Origin': 'http://ymt.zjiet.edu.cn',
        'Referer': 'http://ymt.zjiet.edu.cn/campuspass/start/index.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50',
        'X-Requested-With': 'XMLHttpRequest'
    }
    logindata = {
        'username':id,'password':password
    }
    try:
        # 尝试登录获取token
        r = requests.post(loginurl,json.dumps(logindata),headers=loginheaders)
    except:
        return {'code':500,'result':'服务器维护中','timestamp':now2ticks('int')}

    # token获取成功
    if r.status_code == 200:
        loginresult = json.loads(r.text)
        userheaders = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'access_token': loginresult['result']['access_token'],
            'Connection': 'keep-alive',
            'Host': 'ymt.zjiet.edu.cn',
            'Referer': 'http://ymt.zjiet.edu.cn/campuspass/start/index.html',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50',
            'X-Requested-With': 'XMLHttpRequest'
        }
    else:
        # 获取token失败
        return {'code':r.status_code,'message': '登录失败','result':'','timestamp':now2ticks('int')}

    try:
        # 尝试获取学生信息
        u = requests.get(userurl,headers=userheaders)
    except:
        return {'code':500,'result':'服务器维护中','timestamp':now2ticks('int')}

    # 学生信息成功
    if u.status_code == 200:
        userresult = json.loads(u.text)
        college = userresult['result']['dwmc'];update_T = userresult['result']['gxsj'];isBack = userresult['result']['isBlack']
        QRColor = userresult['result']['mzt'];isOnline = userresult['result']['sfzx'];leave_T = userresult['result']['lxsj']
        QRCode = 'http://ymt.zjiet.edu.cn/campuspassng/campuspass/user/code?token=%s' % loginresult['result']['access_token']
        realname = loginresult['result']['userInfo']['realname'];access_token = loginresult['result']['access_token']
        userInfo = {
            'college':college,
            'update_T':update_T,
            'isBack':isBack,
            'QRColor':QRColor,
            'isOnline':isOnline,
            'leave_T':leave_T,
            'QRCode':QRCode,
            'id': id,
            'realname': realname,
            'access_token':access_token
        }
        # 获取学生信息成功
        # 写入数据库
        try:
            sql = "INSERT INTO userinfo values('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(QRCode,QRColor,access_token,college,id,isBack,isOnline,leave_T,update_T,realname,now2ticks('int'))
            sqliteDB = sqlite3.connect(DATABASE)
            sqliteDB.execute(sql)
            sqliteDB.commit()
            cur = sqliteDB.execute('SELECT * FROM userinfo')
            print('success',cur.fetchall())
            sqliteDB.close()
        except Exception as error:
            print(error)
            pass

        return {'code':r.status_code,'message': '登录成功','result':userInfo,'timestamp':now2ticks('int')}
    else:
        # 获取学生信息失败
        return {'code':r.status_code,'message': '登录失败','result':'','timestamp':now2ticks('int')}

if __name__ == "__main__":
    #app.run()
    app.run(host='0.0.0.0',port=8080)
