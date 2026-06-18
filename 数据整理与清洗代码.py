#!/usr/bin/env python
# coding: utf-8

# In[4]:


import pandas as pd
import re
import os

# 定义城市列表和对应的文件名（根据你的实际文件名修改）
cities = ['上海', '北京', '武汉', '杭州', '南京']
base_dir = 'D:/job_data'          # 存放CSV的文件夹路径

all_dfs = []
for city in cities:
    file_path = os.path.join(base_dir, f'51job_{city}.csv')
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df['城市'] = city               # 新增一列，标记城市
    all_dfs.append(df)

# 合并所有数据框
df_total = pd.concat(all_dfs, ignore_index=True)
print(f'原始总行数：{len(df_total)}')


# In[12]:


import pandas as pd
import re
import os

# 配置
cities = ['上海', '北京', '武汉', '杭州', '南京']
base_dir = r'D:/job_data'

# 1. 合并并添加“城市”列
all_dfs = []
for city in cities:
    file_path = os.path.join(base_dir, f'51job_{city}.csv')
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df['城市'] = city
    all_dfs.append(df)
df_total = pd.concat(all_dfs, ignore_index=True)
print(f"原始总行数：{len(df_total)}")

# 删除无名的空列
df_total = df_total.dropna(axis=1, how='all')
df_total = df_total.loc[:, ~df_total.columns.str.contains('^Unnamed')]

# 2. 薪资清洗（直接转成带单位的文本）
# ==================== 薪资清洗（修正版） ====================
def parse_salary_to_k(salary_str):
    if pd.isna(salary_str):
        return None
    s = str(salary_str).strip()
    if '-' not in s:
        return None
    left_part, right_part = s.split('-', 1)
    # 清理右边多余部分
    for sep in ['·', ' ', '/']:
        if sep in right_part:
            right_part = right_part.split(sep)[0]
    def to_k(v):
        v = v.strip()
        m = re.search(r'[\d\.]+', v)
        if not m:
            return None
        num = float(m.group())
        if '万' in v:
            return num * 10
        elif '千' in v:
            return num
        else:
            return num * 10  # 默认万
    low = to_k(left_part)
    high = to_k(right_part)
    if low is None or high is None:
        return None
    if '/年' in s or s.endswith('年'):
        low /= 12
        high /= 12
    median = (low + high) / 2
    return f'{median:.1f}千元/月'

df_total['薪资_千元月'] = df_total['薪资区间'].apply(parse_salary_to_k)

# 3. 经验清洗（直接转成带单位的文本）
# ==================== 经验清洗 ====================
def exp_to_years_num(exp_str):
    """返回数值（单位：年）"""
    if pd.isna(exp_str):
        return None
    exp = str(exp_str)
    if '无需经验' in exp or '应届生' in exp:
        return 0
    if '1年及以上' in exp:
        return 1
    if '-' in exp and '年' in exp:
        nums = re.findall(r'[\d\.]+', exp)
        if len(nums) >= 2:
            low = float(nums[0])
            high = float(nums[1])
            return (low + high) / 2
    if '年及以上' in exp:
        nums = re.findall(r'\d+', exp)
        if nums:
            return float(nums[0])
    nums = re.findall(r'\d+', exp)
    if nums:
        return float(nums[0])
    return None

df_total['经验_年_数值'] = df_total['经验要求'].apply(exp_to_years_num)
df_total['经验_年'] = df_total['经验_年_数值'].apply(lambda x: f'{x:.1f}年' if pd.notna(x) else '')

# 4. 学历清洗（保持数值等级，不改变）
edu_level = {'高中': 1, '大专': 2, '本科': 3, '硕士': 4, '博士': 5}
def edu_to_level(edu_str):
    if pd.isna(edu_str):
        return 0
    for key, val in edu_level.items():
        if key in str(edu_str):
            return val
    return 0
df_total['学历_等级'] = df_total['学历要求'].apply(edu_to_level)

# 5. 缺失值填充（不变）
df_total['语言要求'] = df_total['语言要求'].fillna('无要求')
df_total['职能类别'] = df_total['职能类别'].fillna('')
df_total['岗位标签'] = df_total['岗位标签'].fillna('')
df_total['关键字'] = df_total['关键字'].fillna('')
df_total['职位信息'] = df_total['职位信息'].fillna('无描述')
df_total['职位信息'] = df_total['职位信息'].astype(str).str[:20]

# 6. 拆分标签
df_total['岗位标签列表'] = df_total['岗位标签'].apply(lambda x: x.split('; ') if x else [])
df_total['关键字列表'] = df_total['关键字'].apply(lambda x: x.split('; ') if x else [])

# 7. 去重
before = len(df_total)
df_total.drop_duplicates(subset=['岗位名称', '公司名称', '城市'], keep='first', inplace=True)
after = len(df_total)
print(f"去重前：{before}，去重后：{after}，删除重复：{before - after}")

# 8. 保存
output_path = os.path.join(base_dir, '51job_all_cities_cleaned.csv')
df_total.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"清洗完成，保存至：{output_path}")


# In[ ]:




