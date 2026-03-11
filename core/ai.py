import os
import json
import requests
from core.config import cfg
from core.print import print_info, print_error, print_success

def get_ai_config():
    """获取 AI 配置信息"""
    # 智能读取配置，优先从数据库获取，并清理前后空格/换行
    raw_url = cfg.get("AI_API_URL", os.environ.get("MINIMAX_API_URL", "https://api.minimaxi.com/v1/text/chatcompletion_v2"))
    url = raw_url.strip() if raw_url else "https://api.minimaxi.com/v1/text/chatcompletion_v2"
    
    # 降维打击：如果 URL 包含错误的后缀（如 /anthropic 或 /v1/messages），强制重置为正确的 Minimax 路径
    if "/anthropic" in url or "/v1/messages" in url or url.endswith(".com") or url.endswith(".chat") or url.endswith(".io"):
        # 提取域名部分并重新拼接
        domain = url.split("//")[-1].split("/")[0]
        url = f"https://{domain}/v1/text/chatcompletion_v2"
        
    model = cfg.get("AI_MODEL", "MiniMax-Text-01").strip()
    # 核心纠偏：防止用户填入 "minimax" 等无效模型名。MiniMax 2.5 必须使用完整 ID。
    if model.lower() in ["minimax", "minimax2.5", "2.5"]:
        model = "MiniMax-Text-01"
        
    group_id = cfg.get("AI_GROUP_ID", os.environ.get("MINIMAX_GROUP_ID", "")).strip()
    # 核心优化：如果 Group ID 是 "admin" 或空字符串，说明是默认占位符，不应发送给 API
    if group_id.lower() in ["admin", "none", "null", ""]:
        group_id = ""
        
    return {
        "api_key": cfg.get("AI_API_KEY", os.environ.get("MINIMAX_API_KEY", "sk-cp-JtBuPOiHRCgWCPYE7XNcosN5x0BeHpANLEMSXlwUPpZEUuHTmAg85b8-liwq4wqIFgYjdGbAV8DrhsV7mgk1zjb2qwSDs-LD8R1_yaGG9pzHCfNlYcC9R_k")).strip(),
        "url": url,
        "model": model,
        "temperature": float(cfg.get("AI_TEMPERATURE", 0.1)),
        "group_id": group_id
    }

BACKEND_VERSION = "V8-STABLE"

def analyze_article(title: str, content: str) -> dict:
    """
    调用 MiniMax 大模型接口，判断文章的分类。
    支持的分类为：便民服务宣传、运营活动宣传、其他。
    """
    if not title and not content:
        return {"category": "其他", "summary": "无内容无法判断"}
        
    try:
        # 获取动态配置
        ai_cfg = get_ai_config()
        if not ai_cfg["api_key"]:
            print_error("[AI] 未配置 AI_API_KEY，请在设置中配置")
            return {"category": "其他", "summary": "未配置 API Key"}

        # 裁剪文章长度防止 Token 超限 (截取前2000个字符用于判断足够了)
        safe_content = content[:2000] if content else ""
        
        prompt = f"""
请作为一位微信公众号文章的内容审核专家，阅读以下文章的标题 and 部分内容，判断它主打宣传的分类。
你只能从以下三个分类选择其一，并给出一句简短的概括性说明理由：
['便民服务宣传', '运营活动宣传', '其他']

文章标题: {title}
文章内容: {safe_content}
"""

        payload = {
            "model": ai_cfg["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是资深的微信公众号运营专家。请仅返回合法的JSON字符串格式数据，包含'category'、'reason' and 'summary'三个字段。category的值必须是'便民服务宣传'或'运营活动宣传'或'其他'。'reason'字段请用一句话说明分类理由，'summary'字段请对文章内容做一段30-50字的精简总结。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": ai_cfg["temperature"]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ai_cfg['api_key']}"
        }
        # 针对 Minimax V2 接口，提供多重 GroupId 兼容
        if ai_cfg.get("group_id"):
            headers["GroupId"] = ai_cfg["group_id"]
            headers["x-group-id"] = ai_cfg["group_id"]
        
        url = ai_cfg["url"]
        # URL 参数兼容
        if ai_cfg.get("group_id") and "GroupId=" not in url:
            connector = "&" if "?" in url else "?"
            url = f"{url}{connector}GroupId={ai_cfg['group_id']}"

        print_info(f"[AI-DEBUG] Backend version: {BACKEND_VERSION}")
        print_info(f"[AI-DEBUG] Final URL: {url}")
        print_info(f"[AI-DEBUG] Headers: { {k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()} }")
        
        print_info(f"[AI] 正在使用 {ai_cfg['model']} 给文章 '{title}' 打标...")
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            res_json = response.json()
            choices = res_json.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                ai_text = choices[0].get("message", {}).get("content")
                if not ai_text:
                     print_error(f"[AI] 响应中 choices[0].message.content 为空: {res_json}")
                     return {"category": "其他", "summary": "AI 返回内容为空"}
                
                # 强力解析 JSON
                try:
                    import json
                    # 清理可能存在的 Markdown 代码块包裹
                    clean_text = ai_text.strip()
                    if clean_text.startswith("```"):
                        # 尝试提取 ```json ... ``` 或 ``` ... ``` 内部内容
                        import re
                        match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_text, re.DOTALL)
                        if match:
                            clean_text = match.group(1).strip()
                    
                    result = json.loads(clean_text)
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
             return {"category": "其他", "summary": f"AI服务报错({response.status_code}): {response.text[:100]}"}
             
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print_error(f"[AI] 分析文章时发生系统错误:\n{err_msg}")
        return {"category": "其他", "summary": f"系统错误: {str(e)[:50]}"}
