import os
import json
import requests
from core.print import print_info, print_error, print_success

# 可以在配置或环境变量中抽取
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "sk-cp-n7zD9FL6896yMSkGtLGRou4bXKrjUw74sZgfBB5ESsxvuvqYotLVSDzNaWGb2TZZYBhuTxtxFkpXqM5-dPjEDLmRPgDukCboMI6QdNHswHUJ_vXN7xzNM3c")
MINIMAX_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

def analyze_article(title: str, content: str) -> dict:
    """
    调用 MiniMax 大模型接口，判断文章的分类。
    支持的分类为：便民服务宣传、运营活动宣传、其他。
    """
    if not title and not content:
        return {"category": "其他", "summary": "无内容无法判断"}
        
    try:
        # 裁剪文章长度防止 Token 超限 (截取前2000个字符用于判断足够了)
        safe_content = content[:2000] if content else ""
        
        prompt = f"""
请作为一位微信公众号文章的内容审核专家，阅读以下文章的标题和部分内容，判断它主打宣传的分类。
你只能从以下三个分类选择其一，并给出一句简短的概括性说明理由：
['便民服务宣传', '运营活动宣传', '其他']

文章标题: {title}
文章内容: {safe_content}
"""

        payload = {
            "model": "abab6.5-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是资深的微信公众号运营专家。请仅返回合法的JSON字符串格式数据，包含'category'、'reason'和'summary'三个字段。category的值必须是'便民服务宣传'或'运营活动宣传'或'其他'。'reason'字段请用一句话说明分类理由，'summary'字段请对文章内容做一段30-50字的精简总结。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MINIMAX_API_KEY}"
        }
        
        print_info(f"[AI] 正在使用 MiniMax 给文章 '{title}' 打标...")
        response = requests.post(MINIMAX_URL, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            res_json = response.json()
            if "choices" in res_json and len(res_json["choices"]) > 0:
                ai_text = res_json["choices"][0]["message"]["content"]
                # 尝试解析 JSON
                try:
                    result = json.loads(ai_text)
                    valid_categories = ['便民服务宣传', '运营活动宣传', '其他']
                    cat = result.get('category', '其他')
                    if cat not in valid_categories:
                        cat = '其他'
                        
                    return {
                        "category": cat,
                        "reason": result.get('reason', 'AI生成理由缺失'),
                        "summary": result.get('summary', 'AI概括缺失')
                    }
                except json.JSONDecodeError:
                    print_error(f"[AI] JSON 解析失败, AI 返回的内容: {ai_text}")
                    return {"category": "其他", "summary": "AI结果解析异常"}
            else:
                 print_error(f"[AI] API 返回内容异常: {res_json}")
                 return {"category": "其他", "summary": "AI接口响应空内容"}
        else:
             print_error(f"[AI] API 调用失败, 状态码: {response.status_code}, 详情: {response.text}")
             return {"category": "其他", "summary": f"AI接口状态异常: {response.status_code}"}
             
    except Exception as e:
        print_error(f"[AI] 分析文章时发生系统错误: {str(e)}")
        return {"category": "其他", "summary": "调用大模型失败"}
