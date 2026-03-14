#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""插入测试文章数据"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db import Db
from core.models.article import Article
from core.models.feed import Feed
from datetime import datetime

def delete_test_data():
    db = Db("测试数据")
    session = db.get_session_factory()()

    try:
        # 删除测试公众号
        feed_ids = ["test_mp_1", "test_mp_2", "test_mp_3"]
        deleted_feeds = session.query(Feed).filter(Feed.id.in_(feed_ids)).delete(synchronize_session=False)
        print(f"删除了 {deleted_feeds} 个公众号")

        # 删除测试文章
        article_ids = [f"test_article_{int(time.time())}_1", f"test_article_{int(time.time())}_2",
                       f"test_article_{int(time.time())}_3", f"test_article_{int(time.time())}_4",
                       f"test_article_{int(time.time())}_5"]
        # 使用模糊匹配删除
        deleted_articles = session.query(Article).filter(Article.id.like("test_article_%")).delete(synchronize_session=False)
        print(f"删除了 {deleted_articles} 篇文章")

        session.commit()
        print("测试数据已删除")
    except Exception as e:
        session.rollback()
        print(f"删除失败: {e}")
    finally:
        session.close()

def insert_test_articles():
    db = Db("测试数据")

    # 创建表
    db.create_tables()

    session = db.get_session_factory()()

    try:
        # 先检查是否已有公众号数据
        existing_feed = session.query(Feed).limit(1).first()
        if not existing_feed:
            # 插入测试公众号数据
            feeds = [
                Feed(
                    id="test_mp_1",
                    mp_name="科技前沿",
                    mp_cover="https://picsum.photos/200/200?random=10",
                    mp_intro="关注科技发展趋势，分享前沿技术资讯",
                    status=1,
                    sync_time=int(time.time()),
                    update_time=int(time.time()),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    faker_id="fake_mp_1"
                ),
                Feed(
                    id="test_mp_2",
                    mp_name="职场观察",
                    mp_cover="https://picsum.photos/200/200?random=11",
                    mp_intro="职场发展指南，帮你提升职业竞争力",
                    status=1,
                    sync_time=int(time.time()),
                    update_time=int(time.time()),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    faker_id="fake_mp_2"
                ),
                Feed(
                    id="test_mp_3",
                    mp_name="云计算时代",
                    mp_cover="https://picsum.photos/200/200?random=12",
                    mp_intro="云计算架构设计与实践",
                    status=1,
                    sync_time=int(time.time()),
                    update_time=int(time.time()),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    faker_id="fake_mp_3"
                )
            ]
            for feed in feeds:
                session.add(feed)
            print(f"成功插入 {len(feeds)} 个公众号")

        # 测试文章数据
        articles = [
            {
                "id": f"test_article_{int(time.time())}_1",
                "mp_id": "test_mp_1",
                "title": "AI人工智能技术发展趋势深度解析",
                "description": "本文深入探讨了AI技术的最新发展趋势，包括大模型、Agent、多模态等前沿技术的应用前景。",
                "content": "<p>人工智能技术正在快速发展，本文分析了当前AI领域的主要趋势...</p><p>大语言模型的出现标志着AI进入了一个新的发展阶段。</p>",
                "content_html": "<p>人工智能技术正在快速发展，本文分析了当前AI领域的主要趋势...</p><p>大语言模型的出现标志着AI进入了一个新的发展阶段。</p>",
                "pic_url": "https://picsum.photos/400/300?random=1",
                "url": "https://example.com/article/1",
                "publish_time": int(time.time()) - 86400,
                "created_at": datetime.now(),
                "updated_at": int(time.time() * 1000),
                "updated_at_millis": int(time.time() * 1000),
                "status": 1,
                "is_export": 0,
                "is_read": 0,
                "ai_category": "其他",
                "ai_summary": "",
                "ai_tags": ""
            },
            {
                "id": f"test_article_{int(time.time())}_2",
                "mp_id": "test_mp_1",
                "title": "Python编程技巧：提高代码效率的10个方法",
                "description": "分享10个实用的Python编程技巧，帮助开发者写出更高效、更优雅的代码。",
                "content": "<p>Python是一门功能强大的编程语言，本文总结了10个提高代码效率的技巧...</p><p>包括列表推导式、生成器、装饰器等高级用法。</p>",
                "content_html": "<p>Python是一门功能强大的编程语言，本文总结了10个提高代码效率的技巧...</p><p>包括列表推导式、生成器、装饰器等高级用法。</p>",
                "pic_url": "https://picsum.photos/400/300?random=2",
                "url": "https://example.com/article/2",
                "publish_time": int(time.time()) - 172800,
                "created_at": datetime.now(),
                "updated_at": int(time.time() * 1000),
                "updated_at_millis": int(time.time() * 1000),
                "status": 1,
                "is_export": 0,
                "is_read": 0,
                "ai_category": "其他",
                "ai_summary": "",
                "ai_tags": ""
            },
            {
                "id": f"test_article_{int(time.time())}_3",
                "mp_id": "test_mp_2",
                "title": "2024年科技行业就业市场分析报告",
                "description": "全面分析2024年科技行业的就业形势，包括热门岗位、薪资水平、发展前景等。",
                "content": "<p>2024年科技行业继续保持增长态势，本文分析了各细分领域的就业情况...</p><p>AI工程师、数据科学家、前端开发等岗位需求旺盛。</p>",
                "content_html": "<p>2024年科技行业继续保持增长态势，本文分析了各细分领域的就业情况...</p><p>AI工程师、数据科学家、前端开发等岗位需求旺盛。</p>",
                "pic_url": "https://picsum.photos/400/300?random=3",
                "url": "https://example.com/article/3",
                "publish_time": int(time.time()) - 259200,
                "created_at": datetime.now(),
                "updated_at": int(time.time() * 1000),
                "updated_at_millis": int(time.time() * 1000),
                "status": 1,
                "is_export": 0,
                "is_read": 0,
                "ai_category": "其他",
                "ai_summary": "",
                "ai_tags": ""
            },
            {
                "id": f"test_article_{int(time.time())}_4",
                "mp_id": "test_mp_2",
                "title": "区块链技术在金融领域的应用与挑战",
                "description": "探讨区块链技术如何改变传统金融业务，以及面临的监管和技术挑战。",
                "content": "<p>区块链技术作为一项颠覆性创新，正在深刻改变金融行业的运作方式...</p><p>本文详细介绍了DeFi、NFT等热门应用场景。</p>",
                "content_html": "<p>区块链技术作为一项颠覆性创新，正在深刻改变金融行业的运作方式...</p><p>本文详细介绍了DeFi、NFT等热门应用场景。</p>",
                "pic_url": "https://picsum.photos/400/300?random=4",
                "url": "https://example.com/article/4",
                "publish_time": int(time.time()) - 345600,
                "created_at": datetime.now(),
                "updated_at": int(time.time() * 1000),
                "updated_at_millis": int(time.time() * 1000),
                "status": 1,
                "is_export": 0,
                "is_read": 0,
                "ai_category": "其他",
                "ai_summary": "",
                "ai_tags": ""
            },
            {
                "id": f"test_article_{int(time.time())}_5",
                "mp_id": "test_mp_3",
                "title": "云计算架构设计最佳实践指南",
                "description": "提供云计算架构设计的全面指南，包括高可用性、可扩展性、安全性等方面的最佳实践。",
                "content": "<p>云计算已成为企业IT基础设施的核心，本文总结了架构设计的关键原则...</p><p>包括微服务架构、容器化部署、CDN加速等技术要点。</p>",
                "content_html": "<p>云计算已成为企业IT基础设施的核心，本文总结了架构设计的关键原则...</p><p>包括微服务架构、容器化部署、CDN加速等技术要点。</p>",
                "pic_url": "https://picsum.photos/400/300?random=5",
                "url": "https://example.com/article/5",
                "publish_time": int(time.time()) - 432000,
                "created_at": datetime.now(),
                "updated_at": int(time.time() * 1000),
                "updated_at_millis": int(time.time() * 1000),
                "status": 1,
                "is_export": 0,
                "is_read": 0,
                "ai_category": "其他",
                "ai_summary": "",
                "ai_tags": ""
            }
        ]

        for article_data in articles:
            article = Article(**article_data)
            session.add(article)

        session.commit()
        print(f"成功插入 {len(articles)} 条测试文章")

    except Exception as e:
        session.rollback()
        print(f"插入失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        delete_test_data()
    else:
        insert_test_articles()
