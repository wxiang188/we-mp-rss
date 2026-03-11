import threading
from fastapi import APIRouter, Depends
from apis.base import error_response
from core.auth import get_current_user
from core.db import DB
from core.models.article import Article
from core.ai import analyze_article
from core.print import print_info, print_success, print_error
import time
import uuid

router = APIRouter(prefix="/ai", tags=["AI"])

# 任务锁，防止并发启动多个任务
_task_lock = threading.Lock()

# 分类状态存储
classify_status = {
    "running": False,
    "completed": False,
    "progress": "",
    "logs": [],
    "total": 0,
    "processed": 0,
    "task_id": None  # 任务唯一标识
}

def reset_classify_status():
    """重置分类状态"""
    classify_status["running"] = False
    classify_status["completed"] = False
    classify_status["progress"] = ""
    classify_status["logs"] = []
    classify_status["total"] = 0
    classify_status["processed"] = 0
    classify_status["task_id"] = None

def run_classify_task():
    """后台执行AI分类任务"""
    # 获取当前任务ID，用于判断任务是否过期
    current_task_id = classify_status["task_id"]

    session = DB.get_session()

    try:
        # 再次检查任务是否仍是当前任务（防止并发问题）
        if classify_status["task_id"] != current_task_id:
            print_info("检测到新任务，跳过当前任务")
            return

        # 查询未分类的文章
        articles = session.query(Article).filter(
            (Article.ai_category == None) | (Article.ai_category == '') | (Article.ai_category == '其他')
        ).all()

        if not articles:
            classify_status["progress"] = "所有文章都已经打过 AI 标签，无需分类！"
            classify_status["logs"].append(classify_status["progress"])
            classify_status["completed"] = True
            classify_status["running"] = False
            return

        classify_status["total"] = len(articles)
        classify_status["progress"] = f"共发现 {len(articles)} 篇文章需要分类"
        classify_status["logs"].append(classify_status["progress"])

        success_count = 0
        for idx, art in enumerate(articles, 1):
            # 检查任务是否已被替换
            if classify_status["task_id"] != current_task_id:
                classify_status["logs"].append("任务已终止")
                classify_status["running"] = False
                break

            classify_status["progress"] = f"正在分析第 {idx}/{len(articles)} 篇: {art.title[:20]}..."
            classify_status["logs"].append(classify_status["progress"])
            classify_status["processed"] = idx

            try:
                content_text = art.content_html or art.content or art.description
                if not content_text and not art.title:
                    continue

                ai_res = analyze_article(art.title, content_text)
                art.ai_category = ai_res.get('category', '其他')
                art.ai_summary = ai_res.get('summary', '')
                art.ai_tags = ai_res.get('ai_tags', '')

                session.commit()
                success_count += 1
                classify_status["logs"].append(f"完成: {art.ai_category} - {art.title[:30]}")

                time.sleep(1)
            except Exception as e:
                classify_status["logs"].append(f"错误: {str(e)}")

        # 只有当前任务完成时才更新最终状态
        if classify_status["task_id"] == current_task_id:
            classify_status["progress"] = f"分类完成！成功打标 {success_count} 篇文章"
            classify_status["logs"].append(classify_status["progress"])
            classify_status["completed"] = True
            classify_status["running"] = False

    except Exception as e:
        classify_status["progress"] = f"分类失败: {str(e)}"
        classify_status["logs"].append(f"失败: {str(e)}")
        classify_status["completed"] = True
        classify_status["running"] = False
    finally:
        session.close()

@router.post("/classify", summary="开始AI文章分类")
async def start_ai_classify(current_user=Depends(get_current_user)):
    """触发AI文章分类任务"""
    # 使用锁防止并发启动多个任务
    with _task_lock:
        if classify_status["running"]:
            return error_response("分类任务正在运行中")

        # 生成新的任务ID
        new_task_id = str(uuid.uuid4())
        reset_classify_status()
        classify_status["task_id"] = new_task_id
        classify_status["running"] = True

        # 启动后台任务
        thread = threading.Thread(target=run_classify_task)
        thread.daemon = True
        thread.start()

    return {"code": 0, "msg": "分类任务已启动", "success": True}

@router.get("/classify/status", summary="获取AI分类状态")
async def get_classify_status(current_user=Depends(get_current_user)):
    """获取AI分类任务状态"""
    # 计算百分比，确保不超过 100%
    percent = 0
    if classify_status["total"] > 0:
        percent = min(100, int(classify_status["processed"] / classify_status["total"] * 100))

    return {
        "code": 0,
        "running": classify_status["running"],
        "completed": classify_status["completed"],
        "progress": classify_status["progress"],
        "logs": classify_status["logs"][-20:],
        "total": classify_status["total"],
        "processed": classify_status["processed"],
        "percent": percent  # 新增：返回计算好的百分比
    }
