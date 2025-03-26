"""
懂车帝二手车信息爬虫

该脚本用于爬取懂车帝网站的二手车信息，通过破解字体反爬机制获取真实数据，
并将数据存储到MySQL数据库中。
"""

import requests
import mysql.connector
from utils.parse_woff_font import extract_text_from_font


def get_data_mapping(font_path):
    """
    从字体文件中提取字符映射关系
    
    Args:
        font_path: 字体文件路径
        
    Returns:
        字典，键为加密字符，值为实际数字或文字
    """
    data_mapping = {}
    # 使用parse_woff_font模块提取字体映射
    for key, value in extract_text_from_font(font_path).items():
        # 将'uni'格式的键转换为对应的Unicode字符
        data_mapping[chr(int(key[3:], 16))] = value
    print(data_mapping)
    return data_mapping


def change_price(original_price: str, data_mapping):
    """
    将加密的价格转换为真实价格
    
    Args:
        original_price: 加密的价格字符串
        data_mapping: 字符映射字典
        
    Returns:
        解密后的价格字符串
    """
    result = ""
    for item in original_price:
        # 保留小数点，替换其他字符
        if item == ".":
            result += item
        else:
            result += data_mapping[item]
    return result


def change_sub_title(original_sub_title: str, data_mapping):
    """
    将加密的副标题转换为真实文本
    
    Args:
        original_sub_title: 加密的副标题字符串
        data_mapping: 字符映射字典
        
    Returns:
        解密后的副标题字符串
    """
    result = ""
    for i in original_sub_title:
        # 保留特殊字符，替换其他字符
        if i == "." or i == "|" or i == " ":
            result += i
        else:
            result += data_mapping[i]
    return result


def insert_data(data_list):
    """
    将爬取的车辆数据插入到MySQL数据库
    
    Args:
        data_list: 包含车辆信息的字典列表
    """
    # 创建数据库连接
    db = mysql.connector.connect(
        host="localhost",  # MySQL服务器地址
        user="root",  # 用户名
        password="",  # 密码
        database="crawler"  # 数据库名称
    )

    # 创建游标对象，用于执行SQL查询
    cursor = db.cursor()
    try:
        for data in data_list:
            # 插入数据
            sql = "INSERT INTO donchedi (title, sub_title, transfer_cnt, official_price, sh_price) VALUES (%s, %s, %s, %s, %s)"
            val = (data['title'], data['sub_title'], data['transfer_cnt'], data['official_price'], data['sh_price'])
            cursor.execute(sql, val)
        # 提交事务
        db.commit()
        print(f"成功插入 {len(data_list)} 条数据")
    except Exception as e:
        print(f"数据插入失败: {e}")
        db.rollback()  # 发生错误时回滚事务

    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def get_font(font_path):
    """
    下载懂车帝使用的加密字体文件
    
    Args:
        font_path: 保存字体文件的本地路径
    """
    # 设置请求头，模拟浏览器访问
    headers = {
        'Origin': 'https://www.dongchedi.com',
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://www.dongchedi.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
    }

    # 发送GET请求下载字体文件
    response = requests.get('https://lf6-awef.bytetos.com/obj/awesome-font/c/96fc7b50b772f52.woff2', headers=headers)

    # 保存字体文件到本地
    with open(font_path, 'wb') as f:
        f.write(response.content)
    
    print(f"字体文件已下载到: {font_path}")


def get_data_list(data_mapping):
    """
    获取懂车帝二手车列表数据
    
    Args:
        data_mapping: 字符映射字典，用于解密数据
        
    Returns:
        包含车辆信息的字典列表
    """
    # 模拟浏览器Cookie
    cookies = {
        'ttwid': '1%7CKNNgoGKVQPJc7f62q4IPZPB57vV3dXjmv0zJszLOo38%7C1742919269%7Cd302f7092340522b30f783673d28d18a04713517528db18c206b8306b56c5f8d',
        'tt_webid': '7485781164335433241',
        'tt_web_version': 'new',
        's_v_web_id': 'verify_m8op4rqa_JMwwnnms_yuXd_4kXk_Banh_2fS8rD1OH7P5',
        '_gid': 'GA1.2.801298683.1742919271',
        'city_name': '%E6%9D%AD%E5%B7%9E',
        'is_dev': 'false',
        'is_boe': 'false',
        'Hm_lvt_3e79ab9e4da287b5752d8048743b95e6': '1742919269,1742956136',
        'HMACCOUNT': '8F8909929AD5C26B',
        '_ga_YB3EWSDTGF': 'GS1.1.1742956136.2.1.1742957589.60.0.0',
        'Hm_lpvt_3e79ab9e4da287b5752d8048743b95e6': '1742957590',
        '_ga': 'GA1.2.320226165.1742919271',
        '_gat_gtag_UA_138671306_1': '1',
    }

    # 设置请求头
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.dongchedi.com',
        'priority': 'u=1, i',
        'referer': 'https://www.dongchedi.com/usedcar/x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'x-forwarded-for': '',
        # 'cookie': '...',  # 已通过cookies参数传递
    }

    # 设置请求参数
    params = {
        'aid': '1839',
        'app_name': 'auto_web_pc',
    }

    # 请求数据，设置全国范围，第1页，每页20条
    data = '&sh_city_name=全国&page=1&limit=20'.encode()

    # 发送POST请求获取二手车列表数据
    response = requests.post(
        'https://www.dongchedi.com/motor/pc/sh/sh_sku_list',
        params=params,
        cookies=cookies,
        headers=headers,
        data=data,
    )

    # 解析响应数据
    data_list = []
    for data in response.json()['data']['search_sh_sku_info_list']:
        # 提取车辆信息并解密
        title = data['title']  # 标题通常不加密
        sub_title = change_sub_title(data['sub_title'], data_mapping)  # 解密副标题
        transfer_cnt = data['transfer_cnt']  # 过户次数
        official_price = change_price(data['official_price'], data_mapping)  # 解密官方指导价
        sh_price = change_price(data['sh_price'], data_mapping)  # 解密二手车价格
        
        # 将解密后的数据添加到结果列表
        data_list.append({
            "title": title, 
            "sub_title": sub_title, 
            "transfer_cnt": transfer_cnt, 
            "official_price": official_price,
            "sh_price": sh_price
        })
    
    print(f"成功获取 {len(data_list)} 条车辆信息")
    return data_list


def main():
    """
    主函数，协调各个步骤的执行
    """
    # 字体文件保存路径
    font_path = 'font.woff2'
    
    # 下载字体文件
    get_font(font_path)
    
    # 解析字体映射关系
    data_mapping = get_data_mapping(font_path)
    
    # 获取二手车数据
    data_list = get_data_list(data_mapping)
    
    # 将数据插入数据库
    insert_data(data_list)
    
    print("爬取完成！数据已成功存入数据库。")


if __name__ == '__main__':
    main()

"""
使用说明与注意事项
==============

1. 数据库准备:
   在运行此脚本前，需要在MySQL中创建名为"crawler"的数据库，并创建"donchedi"表，表结构如下:
   
   ```sql
   CREATE TABLE donchedi (
       id INT AUTO_INCREMENT PRIMARY KEY,
       title VARCHAR(255),
       sub_title VARCHAR(255),
       transfer_cnt INT,
       official_price VARCHAR(50),
       sh_price VARCHAR(50),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. 环境依赖:
   - 需安装: requests, mysql-connector-python 
   - 需自定义模块: utils.parse_woff_font

3. 反爬机制说明:
   懂车帝网站采用自定义字体映射进行数据加密，主要针对价格和车辆信息。
   本脚本通过下载并解析其字体文件来破解这一保护机制。

4. 可扩展功能:
   - 增加翻页功能获取更多数据
   - 添加车型、价格区间等筛选条件
   - 实现定时任务，定期更新数据
   - 添加代理IP池，避免请求频率限制

5. 注意事项:
   - 请合理控制爬取频率，避免对目标网站造成负担
   - 字体文件可能会定期更新，需要关注映射变化
   - Cookie可能会过期，需要定期更新

6. 免责声明:
   本代码仅用于学习交流，请勿用于商业用途。
   使用本代码产生的任何后果由使用者自行承担。
"""
