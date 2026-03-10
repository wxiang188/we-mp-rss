import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.db import DB
from jobs.article import UpdateArticle

article_data = {
    'id': 'test_article_12345',
    'mp_id': 'test_mp_id',
    'title': 'Test Article',
    'pic_url': '',
    'publish_time': 1672531200,
    'created_at': '2023-01-01 00:00:00',
    'updated_at': '2023-01-01 00:00:00',
    'content': '<p>This is a test article.</p>',
    'is_export': 0,
}

print("Running test insert...")
res = UpdateArticle(article_data)
print(f"Result: {res}")
