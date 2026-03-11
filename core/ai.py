import os
import requests
import json
import re
from core.config import get_config
from core.utils import print_info, print_error

# 核心配置：使用用户提供的固定 Key 和 Anthropic 协议
AI_API_KEY = "sk-cp-JtBuPOiHRCgWCPYE7XNcosN5x0BeHpANLEMSXlwUPpZEUuHTmAg85b8-liwq4wqIFgYjdGbAV8DrhsV7mgk1zjb2qwSDs-LD8R1_yaGG9pzHCfNlYcC9R_k"
AI_ENDPOINT = "https://api.minimax.chat/anthropic/v1/messages"
AI_MODEL = "MiniMax-M2.5"
BACKEND_VERSION = "V10-ANTHROPIC-STABLE"

def analyze_article(title: str, content: str) -> dict:
    """
    使用 MiniMax Anthropic 兼容接口进行文章分析总结。
    """
    try:
        # 构建适合 Anthropic 协议的消息结构
        prompt = f"标题: {title}\n内容: {content[:1000]}"
        
        payload = {
            "model": AI_MODEL,
            "max_tokens": 1024,
            "temperature": 0.1,
            "system": "你是资深的微信公众号运营专家。请仅返回合法的JSON字符串格式数据，包含'category'、'reason'和'summary'三个字段。category的值必须是'便民服务宣传'或'运营活动宣传'或'其他'。'reason'字段请用一句话说明分类理由，'summary'字段请对文章内容做一段30-50字的精简总结。",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        headers = {
            "x-api-key": AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        print_info(f"[AI-DEBUG] Version: {BACKEND_VERSION}")
        print_info(f"[AI-DEBUG] URL: {AI_ENDPOINT}")
        print_info(f"[AI] 正在使用 Anthropic 协议 ({AI_MODEL}) 给文章 '{title}' 打标...")
        
        response = requests.post(AI_ENDPOINT, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            res_json = response.json()
            # Anthropic 协议的响应在 content[0].text
            content_list = res_json.get("content", [])
            if content_list and len(content_list) > 0:
                ai_text = content_list[0].get("text", "")
                if not ai_text:
                    return {"category": "其他", "summary": "AI 返回文本为空"}
                
                # 强力解析 JSON（兼容 Markdown 代码块）
                try:
                    clean_text = ai_text.strip()
                    if clean_text.startswith("```"):
                        match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_text, re.DOTALL)
                        if match:
                            clean_text = match.group(1).strip()
                    
                    result = json.loads(clean_text)
                    return {
                        "category": result.get("category", "其他"),
                        "summary": result.get("summary", ai_text[:50])
                    }
                except Exception as e:
                    print_error(f"[AI] JSON 解析失败: {e}, 原文: {ai_text}")
                    return {"category": "其他", "summary": ai_text[:50]}
            else:
                print_error(f"[AI] 响应内容为空结构: {res_json}")
                return {"category": "其他", "summary": "AI 未返回有效内容"}
        else:
            print_error(f"[AI] API 调用失败, 状态码: {response.status_code}, 详情: {response.text}")
            return {"category": "其他", "summary": f"API 错误: {response.status_code}"}
            
    except Exception as e:
        import traceback
        print_error(f"[AI] 发生系统错误: {str(e)}\n{traceback.format_exc()}")
        return {"category": "其他", "summary": f"系统错误: {str(e)}"}
