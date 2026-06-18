# 导入依赖库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import warnings
warnings.filterwarnings('ignore')

# ===================== 全局配置：彻底解决中文乱码、负号异常 =====================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (10, 6)

# ===================== 1 读取CSV数据 =====================
file_path = r'D:\桌面\python\51job_all_cities_cleaned.csv'
df = pd.read_csv(file_path, encoding='utf-8-sig')

print("=" * 60)
print(f"【原始数据总行数】：{len(df)}")
print("【数据所有字段】：")
print(df.columns.tolist())
print("=" * 60)

# 核心字段预览
check_cols = ['工作城市', '薪资_千元月', '学历要求', '经验_年', '公司性质']
print("【核心字段样例】")
print(df[check_cols].head(10))
print("=" * 60)

# ===================== 2 数据清洗（薪资专项处理） =====================
# 填充空文本字段
df['岗位标签'] = df['岗位标签'].fillna('')
df['关键字'] = df['关键字'].fillna('')
df['语言要求'] = df['语言要求'].fillna('无')

# 薪资字段深度清洗
def clean_salary(val):
    if pd.isna(val) or str(val).strip() == '':
        return np.nan
    res = re.findall(r'\d+\.?\d*', str(val))
    if res:
        return float(res[0])
    else:
        return np.nan

df['薪资_clean'] = df['薪资_千元月'].apply(clean_salary)

# 过滤有效薪资
df_valid = df[df['薪资_clean'] > 0].copy()
print(f"【清洗后有效薪资数据行数】：{len(df_valid)}")
print(f"【薪资范围】：{df_valid['薪资_clean'].min()} ~ {df_valid['薪资_clean'].max()} 千元/月")
print("=" * 60)

if len(df_valid) == 0:
    print("❌ 错误：无有效薪资数据，请检查原始CSV文件！")
    exit()

# ===================== 3 可视化绘图（仅弹窗展示，不保存图片） =====================
def set_plot_style():
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

# -------- 图表1：薪资分布直方图 --------
print("正在绘制：薪资分布直方图")
plt.figure()
plt.hist(df_valid['薪资_clean'], bins=25, color='skyblue', edgecolor='black', range=(0, 100))
plt.title('岗位薪资分布直方图')
plt.xlabel('薪资（千元/月）')
plt.ylabel('岗位数量')
set_plot_style()
plt.show()

# -------- 图表2：主要城市平均薪资柱状图 --------
print("正在绘制：各城市平均薪资对比")
city_count = df_valid['工作城市'].value_counts().head(10)
city_salary = df_valid[df_valid['工作城市'].isin(city_count.index)].groupby('工作城市')['薪资_clean'].mean().sort_values(ascending=False)

plt.figure()
plt.bar(city_salary.index, city_salary.values, color='#4F94CD')
plt.title('主要城市岗位平均薪资')
plt.xlabel('城市')
plt.ylabel('平均薪资（千元/月）')
plt.xticks(rotation=45)
set_plot_style()
plt.show()

# -------- 图表3：不同学历薪资箱线图 --------
print("正在绘制：不同学历薪资分布")
edu_list = df_valid['学历要求'].dropna().unique()
edu_filter = [edu for edu in edu_list if len(df_valid[df_valid['学历要求'] == edu]) >= 5]

plt.figure()
box_data = [df_valid[df_valid['学历要求'] == edu]['薪资_clean'] for edu in edu_filter]
plt.boxplot(box_data, labels=edu_filter, patch_artist=True, boxprops=dict(facecolor='lightgreen'))
plt.title('不同学历薪资分布箱线图')
plt.xlabel('学历要求')
plt.ylabel('薪资（千元/月）')
set_plot_style()
plt.show()

# -------- 图表4：工作经验占比饼图 --------
print("正在绘制：工作经验要求分布")
exp_count = df_valid['经验_年'].value_counts()

plt.figure(figsize=(8,8))
plt.pie(exp_count.values, labels=exp_count.index, autopct='%1.1f%%', startangle=90)
plt.title('岗位工作经验要求占比')
plt.axis('equal')
plt.tight_layout()
plt.show()

# -------- 新增图表5：学历要求占比饼状图 --------
print("正在绘制：学历要求分布饼图")
edu_pie_data = df_valid['学历要求'].value_counts()
plt.figure(figsize=(8,8))
plt.pie(edu_pie_data.values, labels=edu_pie_data.index, autopct='%1.1f%%', startangle=90)
plt.title('岗位学历要求分布占比')
plt.axis('equal')
plt.tight_layout()
plt.show()

# ------- 图表6：不同公司性质平均薪资柱状图 -------
print("正在绘制：不同公司性质平均薪资")

# 1. 先按原数据分组
company_salary_all = df_valid.groupby('公司性质')['薪资_clean'].mean().sort_values(ascending=False)

# 2. 定义要保留的类别列表
keep_types = [
    "外企代表处",
    "已上市",
    "国企",
    "事业单位",
    "创业公司",
    "民营",
    "外资（欧美）",
    "外资（非欧美）",
    "合资"
]

# 3. 过滤出你要的类别
company_salary = company_salary_all[company_salary_all.index.isin(keep_types)]

# 4. 绘图
plt.figure()
plt.bar(company_salary.index, company_salary.values, color='#7CCD7C')
plt.title('不同公司性质平均薪资对比')
plt.xlabel('公司性质')
plt.ylabel('平均薪资（千元/月）')
plt.xticks(rotation=45)
set_plot_style()
plt.show()

print("\n✅ 所有图表绘制完成！")