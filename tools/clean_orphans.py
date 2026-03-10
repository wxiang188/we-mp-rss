import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import DB
from core.models.feed import Feed
from core.models.article import Article
from core.print import print_info, print_success, print_error

def run_clean():
    session = DB.get_session()
    try:
        # Find all MP IDs that exist in the Feeds table
        subquery = session.query(Feed.id).subquery()
        
        # Delete articles whose mp_id is not in the subquery
        deleted_count = session.query(Article)\
            .filter(~Article.mp_id.in_(subquery))\
            .delete(synchronize_session=False)
            
        session.commit()
        print_success(f"清理成功！共清除了 {deleted_count} 篇由于删除原公众号而残留的孤儿文章记录。")
    except Exception as e:
        session.rollback()
        print_error(f"清理失败: {e}")

if __name__ == "__main__":
    run_clean()
