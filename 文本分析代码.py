# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
from collections import Counter
import re
import os
import warnings
import platform

warnings.filterwarnings('ignore')

# ==================== 1. 设置中文显示 ====================
system = platform.system()
if system == 'Windows':
    FONT_PATH = 'C:/Windows/Fonts/simhei.ttf'
elif system == 'Darwin':  # Mac
    FONT_PATH = '/System/Library/Fonts/PingFang.ttc'
else:  # Linux
    FONT_PATH = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'

plt.rcParams['font.sans-serif'] = ['SimHei'] if system == 'Windows' else ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 2. 创建输出目录 ====================
output_dir = './output_charts'
os.makedirs(output_dir, exist_ok=True)

# ==================== 3. 读取并合并数据 ====================
cities = ['南京', '武汉', '杭州', '北京', '上海']
dfs = []
for city in cities:
    file_name = f'{city}汇总.xlsx'
    try:
        df_city = pd.read_excel(file_name, sheet_name=0)
        df_city['城市'] = city
        dfs.append(df_city)
        print(f'成功读取 {file_name}，行数：{len(df_city)}')
    except Exception as e:
        print(f'读取 {file_name} 失败：{e}')
if not dfs:
    raise FileNotFoundError('未找到任何数据文件，请检查文件是否存在')
df = pd.concat(dfs, ignore_index=True)
print(f'\n总数据量：{len(df)} 行')

# ==================== 4. 定义停用词和分词函数 ====================
stopwords = set(['的', '了', '是', '在', '和', '与', '或', '有', '我', '你', '它',
                 '我们', '你们', '他们', '招聘', '岗位', '职位', '职责', '工作',
                 '要求', '任职', '资格', '描述', '不限', '学历', '经验', '优先',
                 '薪资', '面议', '福利', '待遇', '培训', '五险一金', '年终奖',
                 '员工', '公司', '以上', '以下', '进行', '负责', '能够', '具有',
                 '相关', '专业', '能力', '良好的', '团队', '协作', '沟通', '等',
                 '工作内容', '职责描述', '岗位职责', '任职要求', '职位描述',
                 '我们提供', '加入我们', '职位亮点', '工作职责', '任职资格'])

def cut_words(text):
    words = jieba.cut(text)
    return ' '.join([w for w in words if len(w) > 1 and w not in stopwords])

# ==================== 5. 生成关键词词云（来自“关键字”列） ====================
print('\n生成“关键词词云”（基于“关键字”列）...')
keywords_text = ' '.join(df['关键字'].fillna('').astype(str))
keywords_cut = cut_words(keywords_text)
if keywords_cut.strip():
    try:
        wc_keywords = WordCloud(font_path=FONT_PATH,
                                width=800, height=600, background_color='white',
                                max_words=150, collocations=False).generate(keywords_cut)
        plt.figure(figsize=(10, 8))
        plt.imshow(wc_keywords, interpolation='bilinear')
        plt.axis('off')
        plt.title('关键词词云（来自“关键字”字段）')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/keywords_wordcloud.png')
        plt.close()
        print('关键词词云已保存至 output_charts/keywords_wordcloud.png')
    except Exception as e:
        print('生成关键词词云失败：', e)
else:
    print('“关键字”字段为空，无法生成关键词词云。')

# ==================== 6. 生成岗位核心福利词云 ====================
print('\n生成“岗位核心福利词云”（从岗位标签、职位信息中提取福利）...')
welfare_keywords = {
    '五险一金', '六险一金', '七险一金', '补充医疗保险', '补充公积金', '企业年金',
    '带薪年假', '带薪病假', '带薪婚假', '带薪产假', '带薪陪产假', '带薪丧假',
    '年终奖金', '绩效奖金', '项目奖金', '股票期权', '股权激励', '分红', '提成', '全勤奖',
    '餐饮补贴', '交通补贴', '通讯补贴', '住房补贴', '租房补贴', '购房补贴', '电脑补贴',
    '高温补贴', '采暖补贴', '工龄补贴', '学历补贴', '技能补贴',
    '免费班车', '免费工作餐', '免费住宿', '提供宿舍', '包吃', '包住', '包吃包住',
    '员工旅游', '定期体检', '专业培训', '技能培训', '系统培训', '入职培训',
    '弹性工作', '周末双休', '做五休二', '朝九晚五', '不加班',
    '节日福利', '生日福利', '结婚礼金', '生育礼金', '丧葬抚恤金', '慰问金',
    '员工活动', '团建', '下午茶', '零食', '健身房', '图书馆', '母婴室',
    '晋升空间', '职业发展', '管理规范', '人性化', '氛围好', '领导nice',
    '国际化', '出国机会', '外派机会', '落户机会', '人才公寓'
}
welfare_text = ' '.join(df['岗位标签'].fillna('').astype(str) + ' ' + df['职位信息'].fillna('').astype(str))
# 使用正则直接匹配（避免分词遗漏）
welfare_freq = Counter()
for pattern in welfare_keywords:
    count = len(re.findall(pattern, welfare_text))
    if count > 0:
        welfare_freq[pattern] = count
# 如果结果太少，补充一些常见福利的简单计数（防止空图）
if len(welfare_freq) < 5:
    for text in df['岗位标签'].fillna(''):
        if '五险一金' in text:
            welfare_freq['五险一金'] += 1
        if '带薪年假' in text:
            welfare_freq['带薪年假'] += 1
        if '年终奖' in text:
            welfare_freq['年终奖金'] += 1
        if '双休' in text:
            welfare_freq['周末双休'] += 1

if welfare_freq:
    try:
        wc_welfare = WordCloud(font_path=FONT_PATH,
                               width=800, height=600, background_color='white',
                               max_words=80, collocations=False).generate_from_frequencies(welfare_freq)
        plt.figure(figsize=(10, 8))
        plt.imshow(wc_welfare, interpolation='bilinear')
        plt.axis('off')
        plt.title('岗位核心福利词云')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/welfare_wordcloud.png')
        plt.close()
        print('岗位核心福利词云已保存至 output_charts/welfare_wordcloud.png')
    except Exception as e:
        print('生成福利词云失败：', e)
else:
    print('未提取到福利词汇，无法生成福利词云。')

print('\n' + '='*60)
print('任务完成！已生成以下图表：')
print('  1. 关键词词云 (keywords_wordcloud.png)')
print('  2. 岗位核心福利词云 (welfare_wordcloud.png)')
print(f'所有图表已保存至 {output_dir} 目录下。')