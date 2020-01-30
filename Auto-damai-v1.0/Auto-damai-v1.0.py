from os.path import exists
from pickle import dump, load
from time import sleep, time
import json
import copy
from tkinter import  *
from tkinter import scrolledtext
from tkinter import ttk
import threading
import tkinter.messagebox as messagebox
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}

class Auto_damai:
    # params: 场次，票价优先级， 实名者数量, 用户昵称， 购买票数， 官网网址， 目标网址
    def __init__(self, session1, price1, card, user_name, ticket_num, damai_url, target_url):
        self.damai_url = damai_url          #大麦首页
        self.target_url = target_url        #目标网页
        self.user_name = user_name        #用户昵称
        self.session1 = session1                   #场次 对应choose_ticket1 不能大于所选场次数量
        self.price1 = price1             #票档优先级 对应choose_ticket1 不能大于所选票档数量
        self.ticket_num = ticket_num                 #购票数量
        self.card = card                       #购票所需证件数量
        self.max_time = 3  # 最长等待时间
        self.refresh_time = 0.3  # 间隔刷新时间
        self.refresh_flag = False           #判断当前网页是否需要刷新

    def isClassPresent(self, item, name, ret=False):
        try:
            result = item.find_element_by_class_name(name)
            if ret:
                return result
            else:
                return True
        except:
            return False


    def get_cookie(self):  #获取cookie
        self.driver.get(self.damai_url)
        log.insert(END, '****请点击登陆****\n')
        sleep(1)
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:  # 等待网页加载完成
            sleep(1)
        log.insert(END, '****请点击扫码登陆****\n')
        while self.driver.title == '大麦登录':  # 等待扫码完成
            sleep(1)
        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        log.insert(END, '****cookie保存成功****\n')


    def set_cookie(self):   #载入cookie
        try:
            cookies = load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.damai.cn',  # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            log.insert(INSERT, '###载入cookie###\n')
        except Exception as e:
            print(e)


    def login(self):
        if not exists('cookies.pkl'):   #cookie不存在，调用获取cookie的函数
            self.driver = webdriver.Chrome()
            self.get_cookie()
            self.driver.quit()

        chrome_options = webdriver.ChromeOptions()     #不加载图片，加快加载速度
        prefs = {"profile.managed_default_content_settings.images":2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)

        self.driver.get(self.target_url)
        self.set_cookie()
        self.driver.refresh()


    def enter_damai(self):   #登录
        self.login()
        try:
            name = (By.XPATH, "/html/body/div[1]/div/div[3]/div[1]/a[2]/div")
            WebDriverWait(self.driver, self.max_time, self.refresh_time).until(EC.text_to_be_present_in_element(name, self.user_name))
            log.insert(INSERT, '####登陆成功####\n')
        except Exception as e:
            print(e)
            self.driver.quit()
            log.insert(END, '####登陆失败####\n')

    def choose_tickets1(self):     #固定场次和票价的优先级，按照优先级的顺序进行抢票 可抢多张
        log.insert(END, '####开始选票####\n')
        while self.driver.title.find('确认订单') == -1:
            #仔细检查session1不能超过场次的最大数量
            self.refresh_flag = False
            session_price = self.driver.find_elements_by_class_name('perform__order__select')
            for select in session_price:
                if select.find_element_by_class_name('select_left').text == '场次':
                    session = select
                elif select.find_element_by_class_name('select_left').text == '票档':
                    price = select
            session_list = session.find_elements_by_class_name('select_right_list_item')
            session_path1 = "//div[@class='select_right_list']/div[%d]/span[2]"
            session_path2 = "//div[@class='select_right_list']/div[%d]/span[1]"
            #if session_list[self.session1-1].find_element_by_class_name('presell').text == '无票':
            if self.isClassPresent(session_list[self.session1-1], 'presell', True) and session_list[self.session1-1].find_element_by_class_name('presell').text == '无票':
                log.insert(END, '演唱会场次为：{}\n'.format(session_list[self.session1 - 1].find_element_by_xpath(session_path1 % self.session1).text))
                log.insert(END, '****所选场次暂时无票，继续刷新****\n')
                self.driver.refresh()
                continue
            else:
                log.insert(END, '演唱会场次为：{}\n'.format(session_list[self.session1 - 1].find_element_by_xpath(session_path2 % self.session1).text))
                session_list[self.session1-1].click()
            price_list = price.find_elements_by_class_name('select_right_list_item')
            for i in range(len(self.price1)):
                log.insert(END, '所选档位为：{}\n'.format(price_list[self.price1[i]-1].find_element_by_class_name('skuname').text))
                if self.isClassPresent(price_list[self.price1[i]-1], 'notticket', True):
                    log.insert(END, '****当前档位缺货****\n')
                    if  i == len(self.price1)-1:
                        self.refresh_flag = True

                else:
                    price_list[self.price1[i]-1].click()
                    break
            if self.refresh_flag:
                log.insert(END, '****当前所有场次均没有票，继续刷新****\n')
                self.driver.refresh()
                continue

            def add_tickets():
                try:
                    for i in range(self.ticket_num-1):
                        add_button = WebDriverWait(self.driver, self.max_time, self.refresh_time).until(EC.presence_of_element_located((By.XPATH,"//div[@class='cafe-c-input-number']/a[2]")))
                        add_button.click()
                except:
                    log.insert(END, '****票数增加失败****\n')

            buy_button = self.driver.find_element_by_class_name('buybtn')
            if buy_button.text == '立即预订' or buy_button.text == '立即购买':
                add_tickets()
                buy_button.click()
                log.insert(END, '****进入订单页面****\n')
            else:
                log.insert(END, '****尚未开票或缺货，继续刷新****\n')
                self.driver.refresh()


    def submit_tickets(self):          #进入订单页，勾选观影人，提交订单
        customer_list = "//*[@id=\"confirmOrder_1\"]/div[2]/div[2]/div[1]/div[%d]/label/span[1]/input"
        for i in range(self.card):
            while self.driver.find_element_by_xpath(customer_list%(i+1)).get_attribute('aria-checked') == 'false':       #判断观影人是否勾选,感觉效率偏低
                WebDriverWait(self.driver, self.max_time, self.refresh_time).until(EC.presence_of_element_located((By.XPATH, customer_list % (i + 1)))).click()
        sumbit_xpath = " //*[@id=\"confirmOrder_1\"]/div[9]/button"
        sumbit_button = WebDriverWait(self.driver, self.max_time, self.refresh_time).until(EC.presence_of_element_located((By.XPATH,sumbit_xpath)))
        sumbit_button.click()

headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
#开启多线程
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()

#GUI
window = Tk()
window.title('大麦自动抢票')
window.geometry('555x500')

message_flag = True
if not exists('config.json'):
    message_flag = False
else:
    with open('config.json','r') as f:
        message_admin = json.load(f)

#print(message_admin)
Label(window, text='大麦用户名:').place(x=0, y=50)
user_name = Entry(window)
user_name.place(x=70, y=50)
if message_flag:
    user_name.insert(0, message_admin['user_name'])

Label(window, text='演唱会名称:').place(x=0, y=90)
key_word = Entry(window)
key_word.place(x=70, y=90)
if message_flag:
    key_word.insert(0, message_admin['name'])

Label(window, text='演唱会列表:').place(x=0, y=130)
search_list = ttk.Combobox(window, width=18)
search_list.place(x=70, y=130)

Label(window, text='场次:').place(x=35, y=170)
session1 = ttk.Combobox(window, width=18)
session1.place(x=70, y=170)
def get_session(*args):    #获得场次列表
    #url = 'https://detail.damai.cn/item.htm?spm=a2oeg.project.searchtxt.ditem_0.74107a34yG7R3G&id=611057434615'
    js_url = 'https://detail.damai.cn/subpage?itemId=' + id_list[search_list.get()] + '&apiVersion=2.0&dmChannel=pc@damai_pc&bizCode=ali.china.damai&scenario=itemsku&dataType=&dataId=&callback=__jp0'
    response = requests.get(js_url, headers=headers)
    session_str = response.text[6:-1]
    session_json = json.loads(session_str)
    session1_select = []
    if session_json:
        for i in range(len(session_json["performCalendar"]["performViews"])):
                session1_select.append(session_json["performCalendar"]["performViews"][i]['performName'])
        session1_select = tuple(session1_select)
        session1['value'] = session1_select
    else:
        session1['value'] = ('尚未开售')
    session1.delete(0, END)
search_list.bind("<<ComboboxSelected>>",get_session)

id_list = {}
seach_url = 'https://search.damai.cn/searchajax.html?keyword='
def search():
    search_html = requests.get(seach_url+key_word.get(), headers=headers)
    seach_json = json.loads(search_html.text)
    search_list1 = []
    for i in range(len(seach_json['pageData']['resultData'])):
        search_list1.append(seach_json['pageData']['resultData'][i]['nameNoHtml'])
        id_list[seach_json['pageData']['resultData'][i]['nameNoHtml']] = seach_json['pageData']['resultData'][i]['id'][4:]
    search_list['value'] = tuple(search_list1)
    session1.delete(0, END)
    search_list.delete(0,END)
button = Button(window, text='搜索',height=0, command=lambda :thread_it(search())).place(x=218, y=87)

Label(window, text='票档:').place(x=35, y=210)
price1 = Entry(window)
price1.place(x=70, y =210)

Label(window, text='观影人数:').place(x=15, y =250)
card = Entry(window)
card.place(x=70, y=250)

Label(window, text='票数:').place(x=35, y=290)
ticket_num = Entry(window)
ticket_num.place(x=70, y=290)


log = scrolledtext.ScrolledText(window, width=40, height=20,font=("隶书",10))
log.place(x=255, y=50)

def save_message():
    message = {}
    message['name'] = key_word.get()
    message['user_name'] = user_name.get()
    for i in range(len(session1['value'])):
        if session1['value'][i] == session1.get():
            message['session1'] = i+1
            break
    price1_list= price1.get().split(' ')
    try:
        for i in range(len(price1_list)):
            price1_list[i] = int(price1_list[i])
    except:
        messagebox.showerror('error', '票档填写有误，可能末尾有空格')
        return
    message['price1'] = price1_list
    message['card'] = int(card.get())
    message['ticket_num'] = int(ticket_num.get())
    message['target_url'] = "https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.324a1046yMOPfv&id=" + id_list[search_list.get()]
    message['damai_url'] = 'https://www.damai.cn/'
    with open('config.json', 'w') as f:
        json.dump(message,f)
    if not exists('config.json'):
        messagebox.showerror('error', '抢票失败，请重新填写')
    else:
        messagebox.showinfo('提交成功', '抢票信息已提交')
        #window.destroy()

def begin(btn):
    log.delete(0.0, END)
    try:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        # params: 场次，票价优先级， 实名者数量, 用户昵称， 购买票数， 官网网址， 目标网址
        damai = Auto_damai(config['session1'], config['price1'], config['card'], config['user_name'],config['ticket_num'],config['damai_url'], config['target_url'])
        def end():
            try:
                damai.driver.quit()
            except Exception as e:
                print(e)
            log.insert(END,'####已停止抢票####')
            btn.config(text='开始抢票', command=lambda :thread_it(begin, button))
        btn.config(text='停止抢票', command=lambda :thread_it(end))
    except Exception as e:
        print(e)
        log.insert(END, '***初始化失败，请检查信息是否填写正确***\n')
    damai.enter_damai()
    while True:
        try:
            damai.choose_tickets1()
            damai.submit_tickets()
        except Exception as e:
            print(e)
            if damai.driver.title.find('支付宝 - 网上支付 安全快速！') == -1:
                sleep(2)
                damai.driver.get(damai.target_url)
            else:
                log.insert(END, '****抢票成功，请付款****\n')
                sleep(999999999)

Button(window, text='提交', command=save_message).place(x=60, y=330)
#多线程，防止卡死
button = Button(window, text='开始抢票', command=lambda :thread_it(begin, button))
button.place(x=110, y=330)

mainloop()