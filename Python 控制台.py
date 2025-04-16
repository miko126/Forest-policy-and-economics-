import requests
import re
import pandas as pd

# 增加更全面的中文姓氏库和常见的复姓
china_surnames = [
    "Zhang", "Li", "Wang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu",
    "Xu", "Sun", "Hu", "Guo", "He", "Gao", "Lin", "Ma", "Peng", "Ding", "Zhu", "Jiang",
    "Zhao", "Qian", "Cai", "Zeng", "Tan", "Luo", "Ye", "Xie", "Huang", "Wang", "Zheng", "Liu"
    # 这里可以添加更多姓氏和复姓
]

# 常见中文名字的拼音形式，可以再根据实际需求扩展
china_common_pinyin_surnames = [
    "Zhang", "Li", "Wang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu", "Xu",
    "Sun", "Hu", "Guo", "He", "Gao", "Lin", "Ma", "Peng", "Ding"
    # 根据需要扩展
]

# 中国大学名单（这里扩展了很多知名大学，包括地方性大学和重点高校，特别是林业和农业相关院校）
china_universities_list = [
    # 综合性大学
    "Tsinghua University", "Peking University", "Fudan University", "Shanghai Jiao Tong University",
    "Zhejiang University", "Beijing Normal University", "Nanjing University", "Xiamen University", "Wuhan University",
    "Tianjin University", "Harbin Institute of Technology", "South China University of Technology", "Jilin University",
    "Xi'an Jiaotong University", "Beihang University", "University of Science and Technology of China",
    "Northeastern University", "Southeast University", "Central South University", "Shandong University",
    "Nanjing Normal University", "East China Normal University", "Renmin University of China",
    "Xiamen University", "Sun Yat-sen University", "Shenzhen University", "Nanjing Agricultural University",
    "Dalian University of Technology", "Northwestern Polytechnical University", "Chongqing University",

    # 林业和农业专门院校
    "Beijing Forestry University", "Nanjing Forestry University", "Northeastern Forestry University",
    "Zhejiang Agriculture and Forestry University",
    "Fujian Agriculture and Forestry University", "South China Agricultural University",
    "Shanxi Agricultural University",
    "Hunan Agricultural University", "Sichuan Agricultural University", "Jiangxi Agricultural University",
    "Shaanxi Forestry Academy",
    "China Agricultural University", "Huazhong Agricultural University", "Zhejiang Agricultural University",
    "Nanjing Agricultural University",
    "Northwest A&F University", "Inner Mongolia Agricultural University", "Gansu Agricultural University",
    "Heilongjiang Bayi Agricultural University",
    "Shenyang Agricultural University", "Guangxi University", "Shandong Agricultural University",
    "Jilin Agricultural University",
    "Henan Agricultural University", "Changsha University of Science and Technology (Agricultural College)",
    "Tibet Agricultural University",

    # 相关研究机构
    "Chinese Academy of Forestry", "Chinese Academy of Agricultural Sciences",
    "National Forestry and Grassland Administration",
    "Chinese Academy of Agricultural Sciences"
]

# 期刊 ISSN 和 CrossRef API 地址
journal_issn = "1389-9341"  # Forest Policy and Economics ISSN
api_url = f"https://api.crossref.org/journals/{journal_issn}/works"
# 设置参数，筛选2024年发表的文章
params = {
    "filter": "from-pub-date:2021-01-01,until-pub-date:2021-12-31",
    "rows": 1000,  # 最大返回条目数
}


# 检查是否为中文名字的函数
def is_chinese_name(name):
    return bool(re.search('[\u4e00-\u9fff]', name))


# 检测拼音形式的中国名字
def is_chinese_name_extended(name):
    return any(name.startswith(surname) for surname in china_common_pinyin_surnames)


# 判断是否属于中国大学的精确匹配
def is_chinese_affiliation(affiliation):
    for uni in china_universities_list:
        if uni in affiliation:
            return True
    return False


# 请求 API 获取数据
response = requests.get(api_url, params=params)
if response.status_code == 200:
    data = response.json()
else:
    print("请求失败，请检查网络或参数。")
    data = {}

# 统计第一作者为中国学者的文章数量
china_authors_count = 0
articles_data = []

# 解析文章数据
if "message" in data and "items" in data["message"]:
    for item in data["message"]["items"]:
        if "author" in item and len(item["author"]) > 0:
            first_author = item["author"][0]
            author_name = first_author.get("family", "") + " " + first_author.get("given", "")
            affiliations = []
            doi = item.get("DOI", "")
            # 获取作者单位信息
            if "affiliation" in first_author:
                affiliations = [aff["name"] for aff in first_author["affiliation"] if "name" in aff]
            # 如果单位为空，尝试通过 DOI 请求更多详细信息
            if not affiliations and doi:
                doi_api_url = f"https://api.crossref.org/works/{doi}"
                doi_response = requests.get(doi_api_url)
                if doi_response.status_code == 200:
                    doi_data = doi_response.json()
                    if "message" in doi_data and "author" in doi_data["message"]:
                        first_author_doi = doi_data["message"]["author"][0]
                        if "affiliation" in first_author_doi:
                            affiliations = [aff["name"] for aff in first_author_doi["affiliation"] if "name" in aff]
            # 判断是否是中国学者
            is_chinese = False
            for aff in affiliations:
                if is_chinese_affiliation(aff):
                    is_chinese = True
                    break
            # 检测中文名字作为辅助
            if not is_chinese:
                is_chinese = is_chinese_name(author_name) or is_chinese_name_extended(author_name)
            # 存储文章信息
            articles_data.append({
                "title": item.get("title", [""])[0],
                "first_author": author_name,
                "affiliation": ", ".join(affiliations) if affiliations else "N/A",
                "DOI": doi,
                "is_chinese": is_chinese
            })
            if is_chinese:
                china_authors_count += 1

# 输出统计信息
print(f"第一作者为中国学者的文章数量：{china_authors_count}")

# 将结果保存为 Excel 文件
df = pd.DataFrame(articles_data)
df.to_excel('china_authors_articles_with_affiliations_2021.xlsx', index=False, engine='openpyxl')
print("数据已保存为 china_authors_articles_with_affiliations_2021.xlsx")
