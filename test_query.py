import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import DB
from core.models.article import ArticleBase
import time

def test_query():
    session = DB.get_session()
    print("Testing query speed without ai_category filter...")
    start_time = time.time()
    
    query1 = session.query(ArticleBase).filter(ArticleBase.status != 0).order_by(ArticleBase.publish_time.desc()).offset(0).limit(10)
    res1 = query1.all()
    count1 = session.query(ArticleBase).filter(ArticleBase.status != 0).count()
    
    print(f"Base query time: {time.time() - start_time:.4f}s. Rows: {len(res1)}. Total: {count1}")
    
    
    print("\nTesting query speed with ai_category filter...")
    start_time = time.time()
    
    query2 = session.query(ArticleBase).filter(ArticleBase.status != 0).filter(ArticleBase.ai_category == '其他').order_by(ArticleBase.publish_time.desc()).offset(0).limit(10)
    res2 = query2.all()
    count2 = session.query(ArticleBase).filter(ArticleBase.status != 0).filter(ArticleBase.ai_category == '其他').count()
    
    print(f"Filter query time: {time.time() - start_time:.4f}s. Rows: {len(res2)}. Total: {count2}")

if __name__ == "__main__":
    test_query()
