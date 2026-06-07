import asyncio
import csv
import random
import re
import json
from datetime import datetime
from playwright.async_api import async_playwright

# ========== 配置 ==========
KEYWORD = "信息管理与信息系统"
JOB_AREA = "070200"            
START_PAGE = 4               # 起始页码（人工跳转）
NUM_PAGES = 2                # 计划爬取总页数
HEADLESS = False
DETAIL_PAGE_DELAY = (3, 6)

# ========== 详情页解析函数（与你原代码完全相同，此处不再重复，请直接粘贴你的 parse_job_detail）==========
# 注意：该函数需要接受 page 和 url 参数，内部使用 page 对象
async def parse_job_detail(page, url):
    """解析单个职位详情页，返回数据字典"""
    try:
        print(f"  正在解析: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_selector("h1[title]", timeout=10000)
        await asyncio.sleep(random.uniform(2, 4))

        job_data = {}

        # 1. 岗位名称
        title_elem = await page.query_selector("h1[title]")
        job_data['岗位名称'] = await title_elem.inner_text() if title_elem else None

        # 2. 薪资区间
        salary_elem = await page.query_selector("strong")
        job_data['薪资区间'] = await salary_elem.inner_text() if salary_elem else None

        # 3. 工作城市
        city_elem = await page.query_selector(".msg.ltype .type_2, .area")
        job_data['工作城市'] = await city_elem.inner_text() if city_elem else None

        # 4. 经验要求
        exp_elem = await page.query_selector(".msg.ltype .type_3")
        job_data['经验要求'] = await exp_elem.inner_text() if exp_elem else None

        # 5. 学历要求
        edu_elem = await page.query_selector(".msg.ltype .type_4")
        job_data['学历要求'] = await edu_elem.inner_text() if edu_elem else None

        # 6. 语言要求
        lang_elem = await page.query_selector(".msg.ltype .type_6")
        job_data['语言要求'] = await lang_elem.inner_text() if lang_elem else None

        # 7. 岗位标签（福利标签）
        tags = []
        tag_elements = await page.query_selector_all(".job-other .tag, .job-tags .tag, .el-tag, .tags .tag")
        for tag in tag_elements:
            text = (await tag.inner_text()).strip()
            if text:
                tags.append(text)
        job_data['岗位标签'] = "; ".join(tags) if tags else None

        # ---------- 获取职位描述全文（仅用于截取前20字）----------
        desc_elem = await page.query_selector(".job_msg .inbox, .bmsg.job_msg")
        full_desc = await desc_elem.inner_text() if desc_elem else None

        # 职位描述前20字
        if full_desc:
            desc_clean = full_desc.strip()
            desc_short = desc_clean[:20] if len(desc_clean) > 20 else desc_clean
            desc_short = desc_short.replace('\n', ' ').replace('\r', '')
            job_data['职位信息'] = desc_short
        else:
            job_data['职位信息'] = None

        # ---------- 职能类别和关键字（直接从 HTML 的 <a> 标签提取）----------
        all_fp = await page.query_selector_all("p.fp")

        # 职能类别
        func_value = None
        for p in all_fp:
            span = await p.query_selector("span.label")
            if span:
                label = (await span.inner_text()).strip()
                if '职能类别' in label:
                    links = await p.query_selector_all("a")
                    if links:
                        texts = [await link.inner_text() for link in links]
                        func_value = '; '.join(texts) if len(texts) > 1 else texts[0]
                    else:
                        raw = (await p.inner_text()).strip()
                        func_value = raw.replace(label, '').strip()
                    break
        job_data['职能类别'] = func_value

        # 关键字
        kw_value = None
        for p in all_fp:
            span = await p.query_selector("span.label")
            if span:
                label = (await span.inner_text()).strip()
                if '关键字' in label:
                    links = await p.query_selector_all("a")
                    if links:
                        texts = [await link.inner_text() for link in links]
                        kw_value = '; '.join(texts)
                    else:
                        raw = (await p.inner_text()).strip()
                        kw_value = raw.replace(label, '').strip()
                    break
        job_data['关键字'] = kw_value

        # ---------- 公司信息 ----------
        # 公司名称
        company = None
        for selector in [".corp-card .com_name p", ".com_name a", ".cname"]:
            elem = await page.query_selector(selector)
            if elem:
                company = (await elem.inner_text()).strip()
                break
        job_data['公司名称'] = company

        # 获取公司信息中的所有 .at 条目
        at_items = await page.query_selector_all(".corp-card .com_tag p.at")
        if len(at_items) >= 1:
            job_data['公司性质'] = (await at_items[0].inner_text()).strip()
        else:
            job_data['公司性质'] = None

        if len(at_items) >= 2:
            job_data['公司规模'] = (await at_items[1].inner_text()).strip()
        else:
            job_data['公司规模'] = None

        if len(at_items) >= 3:
            industry_elem = at_items[2]
            a_in_industry = await industry_elem.query_selector("a")
            if a_in_industry:
                job_data['所属行业'] = (await a_in_industry.inner_text()).strip()
            else:
                job_data['所属行业'] = (await industry_elem.inner_text()).strip()
        else:
            # 备选
            old_industry = await page.query_selector(".corp-card .bc .dc:first-child")
            if old_industry:
                job_data['所属行业'] = (await old_industry.inner_text()).strip()
            else:
                job_data['所属行业'] = None

        return job_data

    except Exception as e:
        print(f"  解析详情页出错: {e}")
        return None

# ========== 提取当前页 jobId（与你原代码相同）==========
async def get_job_ids_from_current_page(page):
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    job_ids = await page.evaluate('''
        () => {
            const items = document.querySelectorAll('.joblist-item');
            const ids = [];
            for (let item of items) {
                const sensorsDiv = item.querySelector('.joblist-item-job');
                if (sensorsDiv && sensorsDiv.getAttribute('sensorsdata')) {
                    try {
                        const data = JSON.parse(sensorsDiv.getAttribute('sensorsdata'));
                        if (data.jobId) {
                            ids.push(data.jobId);
                        }
                    } catch(e) {}
                }
            }
            return ids;
        }
    ''')
    print(f"  当前页提取到 {len(job_ids)} 个 jobId")
    return job_ids

# ========== 主函数（使用双页面，避免后退）==========
async def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"51job_manual_{timestamp}.csv"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=HEADLESS,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # ----- 创建两个页面 -----
        list_page = await context.new_page()   # 专门用于列表页（搜索结果页）
        detail_page = await context.new_page() # 专门用于详情页

        # 1. 访问首页建立会话
        print("正在访问51job首页...")
        await list_page.goto("https://www.51job.com/", wait_until="domcontentloaded")
        input("若出现验证码请手动处理，完成后按回车继续...")
        await asyncio.sleep(2)

        # 2. 进入搜索列表页（第一页）
        first_url = f"https://we.51job.com/pc/search?keyword={KEYWORD}&searchType=2&jobArea={JOB_AREA}&sortType=0&pageNum=1"
        print(f"访问搜索第一页: {first_url}")
        await list_page.goto(first_url, wait_until="domcontentloaded")
        input("请手动处理可能的验证码，并确保页面正常显示职位列表，然后按回车继续...")
        await list_page.wait_for_selector(".joblist-item", timeout=15000)
        await asyncio.sleep(3)

        # 3. 如果需要从非第1页开始，让用户手动跳转
        if START_PAGE > 1:
            if START_PAGE > 6:
                print(f"⚠️ 起始页 {START_PAGE} 可能不在直接显示的页码按钮中（通常只显示前10页）。")
                print(f"请手动在浏览器中连续点击『下一页』按钮，或点击省略号『...』后选择对应页码，直到到达第 {START_PAGE} 页。")
            input(f"请手动点击页码按钮跳转到第 {START_PAGE} 页，然后按回车继续...")
            await list_page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

        all_jobs = []
        current_page = START_PAGE
        page_count = 0

        while page_count < NUM_PAGES:
            print(f"\n========== 抓取第 {current_page} 页的职位详情 ==========")
            # 从列表页提取 jobId（注意：使用 list_page）
            job_ids = await get_job_ids_from_current_page(list_page)
            if not job_ids:
                print("当前页没有提取到 jobId，可能页面未加载完成，请手动检查后按回车重试...")
                input("按回车继续重试...")
                continue

            detail_urls = [f"https://jobs.51job.com/all/{jid}.html" for jid in job_ids]
            # 使用 detail_page 爬取每个详情页
            for idx, url in enumerate(detail_urls):
                print(f"  爬取详情页 {idx+1}/{len(detail_urls)}: {url}")
                job_info = await parse_job_detail(detail_page, url)
                if job_info and job_info.get('岗位名称'):
                    all_jobs.append(job_info)
                else:
                    print("    失败")
                await asyncio.sleep(random.uniform(*DETAIL_PAGE_DELAY))

            page_count += 1
            if page_count < NUM_PAGES:
                # 人工翻页：提示用户手动点击列表页的“下一页”
                input("请手动在浏览器中的【列表页】点击『下一页』按钮，然后按回车继续抓取下一页...")
                # 等待列表页加载完成
                await list_page.wait_for_load_state("networkidle")
                await list_page.wait_for_selector(".joblist-item", timeout=15000)
                await asyncio.sleep(2)
                current_page += 1
            else:
                print("已达到预设页数，抓取结束")

        # 保存 CSV
        if all_jobs:
            fieldnames = [
                '岗位名称', '公司名称', '公司性质', '公司规模', '所属行业',
                '工作城市', '薪资区间', '经验要求', '学历要求', '语言要求',
                '职能类别', '岗位标签', '关键字', '职位信息'
            ]
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for job in all_jobs:
                    row = {k: job.get(k) for k in fieldnames}
                    writer.writerow(row)
            print(f"\n✅ 成功爬取 {len(all_jobs)} 条数据，保存至 {output_file}")
        else:
            print("未获取到任何有效数据")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())