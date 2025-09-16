#import psycopg2
#from psycopg2 import Error
import requests as rq
from bs4 import BeautifulSoup
prod_tp = "Keyboard"
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests,os
import sys
import sqlite3

def download(path,name,url):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(f'{path}/{name}', 'wb') as handle:
        response = requests.get(url, stream=True)
        if not response.ok:
            print(response)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)

chrome_options = Options()
chrome_options.add_argument('--headless')  
chrome_options.add_argument('--disable-gpu')  

driver = webdriver.Chrome(options=chrome_options)


head = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    }

#change manually
url = "https://www.next.co.uk/shop/gender-women-productaffiliation-accessories/category-bags-category-purses"
gender="Women"
category="Bag"

con = rq.get(url,headers=head)
#with open("xt.txt","w",encoding='utf-8') as file:
#    file.write()

doc = con.content
so = BeautifulSoup(doc,"html.parser")
#print(so.prettify())
mydivs = so.find_all("div",class_="MuiGrid-item")
final = []
cnt = 0
for i in range(min(len(mydivs),1000)):
    try:
        gg = mydivs[i]
        driver.get(gg.a.get('href'))
        driver.implicitly_wait(2)
        pc = driver.page_source
        so1 = BeautifulSoup(pc,"html.parser")
        #print(so1.find("div",class_="partial-description-text"))
        #break
        desc = so1.find("p",class_="MuiTypography-root MuiTypography-body2 pdp-css-19plc96").text.replace("'","")
        color = so1.find("span",class_="MuiTypography-root MuiTypography-body3 pdp-css-13hk9fz").text
        #print(color,desc)
        img = gg.a.img.get('src')
        title = gg.h2.text
        title = title.replace("s®","").replace("'","")
        #print(title)
        if "/" in title:
            continue
        """
        if "coat" in title.lower():
           category = "Coat"
        elif "jacket" in title.lower():
            category = "Jacket"
        else:
            continue
        """
        path = gender+"/"+category
        iname = img.split("/")[-1].split("?")[0]
        download(path,iname,img)
        price = gg.find('div',class_="produc-1kp3g5s").text
        price = price.replace("£","")
        if "-" in price:
            price=price.split("-")[0]
        price = re.findall(r'\d+',price)[0]
        final.append([title,path+"/"+iname,desc,price,category,gender,color])
        if len(final) >=15:
            break
    except Exception as e:
        print(e)
        continue

"""
final = []
for i in mydivs:
    gg = re.search("<a href=.(.*).><img",str(i))
    ok = rq.get(gg.group(1))
    #print(gg.group(1))
    sop = BeautifulSoup(ok.content,"html.parser")
    ggall = []
    my =  sop.find_all("meta")
    for j in my:
        #print(str(j))
        try:
            arr = re.findall("^<meta content=.(.*). property=..*./>$",str(j))
            if arr != []:
                ggall.append(*arr)
        except Exception:
            pass
        #print(len(ggall))
    des = "OK"
    tp = "EMI"
    try:
        io = re.findall("<td  class=.name.>(.*)</td><td class=.value.>(.*)</td>",ok.text)
        des = ""
        for i in io:
            des += i[0]+":"+i[1]+";"
        tp = re.search("<span itemprop=.name.>(.*)</span></a><meta itemprop=.position. content=.2.",ok.text).group(1)
    except Exception:
        pass
    name = ggall[0]
    link = ggall[5]
    
    brand = ggall[6]
    ava = ggall[7]
    price = ggall[9].split('.')[0]
    sku = ggall[-1]
    nop = [name,link,brand,ava,price,sku,des]
    final.append([name,link,brand,ava,price,sku,des,prod_tp])
#print(final[1])
"""   
print("here")
"""
try:
    connection = psycopg2.connect(user="postgres",
                                  password="1234",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="postgres")
    
    cursor = connection.cursor()

    for itm in final:
        q = f'''INSERT INTO recomsys_item(title,img, description, price,category,gender,color
        ) VALUES ('{itm[0]}','{itm[1]}','{itm[2]}','{itm[3]}','{itm[4]}','{itm[5]}','{itm[6]}')'''
        #print(q)
        cursor.execute(q)
    connection.commit()
    #record = cursor.fetchall()
    #print(record)

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
    driver.quit()
"""
try:
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()

    for itm in final:
        q = '''INSERT INTO recomsys_item(title, img, description, price, category, gender, color)
               VALUES (?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(q, (itm[0], itm[1], itm[2], itm[3], itm[4], itm[5], itm[6]))

    connection.commit()

except sqlite3.Error as error:
    print("Error while connecting to SQLite", error)
finally:
    if connection:
        cursor.close()
        connection.close()
        print("SQLite connection is closed")
    driver.quit()
