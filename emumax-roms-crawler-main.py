import base64
import requests
from bs4 import BeautifulSoup
import sqlite3
import time

# 模拟请求头
def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.emumax.com',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
    }

def get_html_content_with_policy(page, delay=1):
    url = f'http://www.emumax.com/roms/0-0-0-0-{page}.html'
    try:
        # 添加延迟以避免频繁请求 （或者选择使用代理IP）
        time.sleep(delay)

        # 发送GET请求获取HTML内容
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()  # 检查请求是否成功

        # 返回HTML内容
        return response.text
    except requests.exceptions.RequestException as e:
        print(f'获取页面{page}时出错：{e}')
        return None

def parse_game_list(html_content):
    game_list = []

    # 使用Beautiful Soup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找所有class为'youxi_frbox'的ul元素
    game_ul_elements = soup.find_all('ul', class_='youxi_frbox')

    # 遍历每个ul元素并提取游戏信息
    for ul_element in game_ul_elements:
        game_info = {
            'title': ul_element.find('h1').find('a').text,
            'url': ul_element.find('h1').find('a')['href'],  # 获取URL
            'image_url': ul_element.find('img')['src'],
            'type': ul_element.find('dd', text=lambda t: t and t.startswith('游戏类型：')).text.split('：', 1)[1],
            'platform': ul_element.find('dd', text=lambda t: t and t.startswith('所属机种：')).text.split('：', 1)[1],
            'company': ul_element.find('dd', text=lambda t: t and t.startswith('出品公司：')).text.split('：', 1)[1],
            'recommendation': ul_element.find('dd', text=lambda t: t and t.startswith('游戏推荐：')).text.split('：', 1)[1],
            'update_time': ul_element.find('span', class_='divbt02_time').text,
            'comments': ul_element.find('span', class_='divbt02_liuyan')['title'],
            'downloads': ul_element.find('span', class_='divbt02_xiazai')['title'],
            'views': ul_element.find('span', class_='divbt02_guankan')['title']
        }
        # 将游戏信息添加到列表中
        game_list.append(game_info)

    return game_list

def create_game_table(conn):
    cursor = conn.cursor()
    # 如果表不存在，则创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            image_url TEXT,
            type TEXT,
            platform TEXT,
            company TEXT,
            recommendation TEXT,
            update_time TEXT,
            comments TEXT,
            downloads TEXT,
            views TEXT
        )
    ''')
    conn.commit()

def insert_game(conn, game):
    print(f'插入{game["title"]}')
    cursor = conn.cursor()
    # 将游戏插入表中
    cursor.execute('''
        INSERT INTO games (title, url, image_url, type, platform, company, recommendation, update_time, comments, downloads, views)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        game['title'],
        game['url'],
        game['image_url'],
        game['type'],
        game['platform'],
        game['company'],
        game['recommendation'],
        game['update_time'],
        game['comments'],
        game['downloads'],
        game['views']
    ))
    conn.commit()

# 获取迅雷链
def get_thunder_url(t, pid, id):
    url = f'http://www.emumax.com/download/xunlei?t={t}&pid={pid}&id={id}'
    # 发送POST请求
    r = requests.post(url, headers=get_headers())
    # 判断是否成功
    if r.json()['code'] != 0:
        return None
    return thunder_encode(r.json()['data']['down_url'])

# 迅雷链解析
def thunder_encode(a):
    b = 'AA'
    c = 'ZZ'
    d = 'thunder://'
    # 将JavaScript代码转换为Python代码
    e = d + base64.b64encode((b + a + c).encode('utf-8')).decode('utf-8')
    return e

def store_games_in_database(games, db_name):
    # 连接SQLite数据库（如果不存在则创建新的）
    conn = sqlite3.connect(db_name)
    
    # 如果表不存在，则创建games表
    create_game_table(conn)

    # 将每个游戏插入数据库
    for game in games:
        insert_game(conn, game)

    # 关闭数据库连接
    conn.close()

def main(total_pages, delay_between_requests, db_name):
    for page_number in range(1, total_pages + 1):
        html_content = get_html_content_with_policy(page_number, delay_between_requests)

        if html_content is not None:
            # 解析HTML内容以获取游戏信息
            games = parse_game_list(html_content)

            # 将解析的游戏信息存储在SQLite数据库中
            store_games_in_database(games, db_name)
        else:
            # 处理获取HTML失败的情况
            print(f'无法获取第{page_number}页的HTML')

if __name__ == '__main__':
    total_pages = 2869
    delay_between_requests = 1
    db_name = 'games_database.db'
    main(total_pages, delay_between_requests, db_name)
