import os
import sys

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import DB
from core.models.article import Article
from core.ai import analyze_article
from core.print import print_info, print_success, print_error
import time

def run_backfill():
    print_info("开始检查未应用 AI 分类的历史文章...")
    session = DB.get_session()
    try:
        # 查询那些没有分类或者分类默认是“其他”的文章
        articles = session.query(Article).filter(
            (Article.ai_category == None) | (Article.ai_category == '其他')
        ).all()
        
        if not articles:
            print_success("所有文章都已经打过 AI 标签，无需回刷！")
            return
            
        print_info(f"共发现 {len(articles)} 篇文章需要补充 AI 分类。")
        
        success_count = 0
        for idx, art in enumerate(articles, 1):
            print_info(f"[{idx}/{len(articles)}] 正在分析文章: {art.title[:30]}...")
            
            # 使用现有逻辑获取文章文本
            content_text = art.content_html or art.content or art.description
            if not content_text and not art.title:
                print_info(f"  -> 文章没有内容，跳过。")
                continue
                
            ai_res = analyze_article(art.title, content_text)
            art.ai_category = ai_res.get('category', '其他')
            art.ai_summary = ai_res.get('summary', '')
            
            # 保存到数据库
            session.commit()
            success_count += 1
            print_success(f"  -> 分类完成: {art.ai_category}")
            
            # 防止频繁请求被 MiniMax 接口限流
            time.sleep(1)
            
        print_success(f"历史数据补充完毕！成功打标 {success_count} 篇文章。")
        
    except Exception as e:
        print_error(f"历史数据回刷过程中出现错误: {e}")
        session.rollback()

if __name__ == "__main__":
    run_backfill()
