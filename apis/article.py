from fastapi import APIRouter, Depends, HTTPException, status as fast_status, Query
from core.auth import get_current_user_or_ak
from core.db import DB
from core.models.base import DATA_STATUS
from core.models.article import Article,ArticleBase
from sqlalchemy import and_, or_, desc
from .base import success_response, error_response
from core.config import cfg
from apis.base import format_search_kw
from core.print import print_warning, print_info, print_error, print_success
from core.cache import clear_cache_pattern
from tools.fix import fix_article
router = APIRouter(prefix=f"/articles", tags=["文章管理"])


    
@router.delete("/clean", summary="清理无效文章(MP_ID不存在于Feeds表中的文章)")
async def clean_orphan_articles(
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        from core.models.article import Article
        
        # 找出Articles表中mp_id不在Feeds表中的记录
        subquery = session.query(Feed.id).subquery()
        deleted_count = session.query(Article)\
            .filter(~Article.mp_id.in_(subquery))\
            .delete(synchronize_session=False)
        
        session.commit()
        
        # 清除相关缓存
        clear_cache_pattern("articles_list")
        clear_cache_pattern("home_page")
        clear_cache_pattern("tag_detail")
        
        return success_response({
            "message": "清理无效文章成功",
            "deleted_count": deleted_count
        })
    except Exception as e:
        session.rollback()
        print(f"清理无效文章错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理无效文章失败"
            )
        )

@router.put("/{article_id}/read", summary="改变文章阅读状态")
async def toggle_article_read_status(
    article_id: str,
    is_read: bool = Query(..., description="阅读状态: true为已读, false为未读"),
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.article import Article
        
        # 检查文章是否存在
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        
        # 更新阅读状态
        article.is_read = 1 if is_read else 0
        session.commit()
        
        # 清除相关缓存
        clear_cache_pattern("articles_list")
        clear_cache_pattern("article_detail")
        clear_cache_pattern("tag_detail")
        
        return success_response({
            "message": f"文章已标记为{'已读' if is_read else '未读'}",
            "is_read": is_read
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"更新文章阅读状态失败: {str(e)}"
            )
        )
    
@router.delete("/clean_duplicate_articles", summary="清理重复文章")
async def clean_duplicate(
    current_user: dict = Depends(get_current_user_or_ak)
):
    try:
        from tools.clean import clean_duplicate_articles
        (msg, deleted_count) =clean_duplicate_articles()
        return success_response({
            "message": msg,
            "deleted_count": deleted_count
        })
    except Exception as e:
        print(f"清理重复文章: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理重复文章"
            )
        )


@router.api_route("", summary="获取文章列表",methods= ["GET", "POST"], operation_id="get_articles_list")
async def get_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None),
    mp_id: str = Query(None),
    has_content:bool=Query(False),
    start_date: str = Query(None, description="发布开始日期 (格式: YYYY-MM-DD)"),
    end_date: str = Query(None, description="发布结束日期 (格式: YYYY-MM-DD)"),
    ai_category: str = Query(None, description="AI文章分类"),
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
      
        
        # 构建查询条件
        query = session.query(ArticleBase)
        if has_content:
            query=session.query(Article)
        if status:
            query = query.filter(Article.status == status)
        else:
            query = query.filter(Article.status != DATA_STATUS.DELETED)
        if mp_id:
            query = query.filter(Article.mp_id == mp_id)
        if ai_category:
            query = query.filter(Article.ai_category == ai_category)
        if search:
            query = query.filter(
               format_search_kw(search)
            )
        import time
        from datetime import datetime
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                start_ts = int(time.mktime(start_dt.timetuple()))
                query = query.filter(Article.publish_time >= start_ts)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
                end_ts = int(time.mktime(end_dt.timetuple()))
                query = query.filter(Article.publish_time <= end_ts)
            except ValueError:
                pass
        
        # 获取总数
        total = query.count()
        query= query.order_by(Article.publish_time.desc()).offset(offset).limit(limit)
        # query= query.order_by(Article.id.desc()).offset(offset).limit(limit)
        # 分页查询（按发布时间降序）
        articles = query.all()
        
        # 打印生成的 SQL 语句（包含分页参数）
        print_warning(query.statement.compile(compile_kwargs={"literal_binds": True}))
                       
        # 提取当前页面的所有的 mp_id
        current_mp_ids = list(set([article.mp_id for article in articles if article.mp_id]))
        
        # 查询公众号名称 (批量查询，避免 N+1 性能问题)
        from core.models.feed import Feed
        mp_names = {}
        if current_mp_ids:
            feeds = session.query(Feed).filter(Feed.id.in_(current_mp_ids)).all()
            mp_names = {feed.id: feed.mp_name for feed in feeds}
        
        # 合并公众号名称到文章列表
        article_list = []
        for article in articles:
            article_dict = article.__dict__
            article_dict["mp_name"] = mp_names.get(article.mp_id, "未知公众号")
            article_list.append(article_dict)
        
        from .base import success_response
        return success_response({
            "list": article_list,
            "total": total
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章列表失败: {str(e)}"
            )
        )

@router.get("/ai-categories/list", summary="获取AI分类列表")
async def get_ai_categories(
    current_user: dict = Depends(get_current_user_or_ak)
):
    """获取系统中已使用的AI分类标签列表"""
    session = DB.get_session()
    try:
        # 获取所有非空的 AI 分类标签
        categories = session.query(Article.ai_category).distinct().filter(
            Article.ai_category.isnot(None),
            Article.ai_category != ''
        ).all()
        # 提取分类名称列表
        category_list = [cat[0] for cat in categories if cat[0]]
        # 如果没有分类，返回默认分类
        if not category_list:
            category_list = ['产品功能', '运营活动', '其他']
        return success_response(data=category_list)
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取AI分类列表失败: {str(e)}"
            )
        )

@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: str,
    content: bool = False,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        article = session.query(Article).filter(Article.id==article_id).filter(Article.status != DATA_STATUS.DELETED).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        return success_response(fix_article(article))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章详情失败: {str(e)}"
            )
        )

@router.post("/{article_id}/analyze", summary="人工触发 AI 分析文章")
async def analyze_article_manually(
    article_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.article import Article
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        
        from core.ai import analyze_article
        ai_res = analyze_article(article.title, article.content_html or article.content or article.description)
        
        # 更新数据库
        article.ai_category = ai_res.get('category', '其他')
        article.ai_reason = ai_res.get('reason', '')
        article.ai_summary = ai_res.get('summary', '')
        session.commit()
        
        return success_response({
            "message": f"文章《{article.title}》分析完成",
            "category": article.ai_category,
            "reason": article.ai_reason,
            "summary": article.ai_summary
        })
    except Exception as e:
        session.rollback()
        print(f"人工AI分析错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"分析失败: {str(e)}"
            )
        )

@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        from core.models.article import Article
        
        # 检查文章是否存在
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        # 逻辑删除文章（更新状态为deleted）
        article.status = DATA_STATUS.DELETED
        if cfg.get("article.true_delete", False):
            session.delete(article)
        session.commit()
        
        return success_response(None, message="文章已标记为删除")
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"删除文章失败: {str(e)}"
            )
        )

@router.get("/{article_id}/next", summary="获取下一篇文章")
async def get_next_article(
    article_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更晚的第一篇文章
        next_article = session.query(Article)\
            .filter(Article.publish_time > current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.asc())\
            .first()
        
        if not next_article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40402,
                    message="没有下一篇文章"
                )
            )
        return success_response(fix_article(next_article))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取下一篇文章失败: {str(e)}"
            )
        )

@router.get("/{article_id}/prev", summary="获取上一篇文章")
async def get_prev_article(
    article_id: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更早的第一篇文章
        prev_article = session.query(Article)\
            .filter(Article.publish_time < current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.desc())\
            .first()
        
        if not prev_article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40403,
                    message="没有上一篇文章"
                )
            )
        return success_response(fix_article(prev_article))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取上一篇文章失败: {str(e)}"
            )
        )