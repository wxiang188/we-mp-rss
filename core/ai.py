import os
import requests
import json
import re
from core.print import print_info, print_error

# 核心配置：V13 饱和式适配版
AI_API_KEY = "sk-cp-JtBuPOiHRCgWCPYE7XNcosN5x0BeHpANLEMSXlwUPpZEUuHTmAg85b8-liwq4wqIFgYjdGbAV8DrhsV7mgk1zjb2qwSDs-LD8R1_yaGG9pzHCfNlYcC9R_k"
# 切换为官方文档推荐的域名
AI_ENDPOINT = "https://api.minimaxi.com/anthropic/v1/messages"
AI_MODEL = "MiniMax-M2.5"
BACKEND_VERSION = "V13-ANTHROPIC-ULTIMATE"

def analyze_article(title: str, content: str) -> dict:
    """
    使用 MiniMax Anthropic 兼容接口进行文章分析总结。
    """
    try:
        prompt = f"标题: {title}\n内容: {content[:1000]}"
        
        payload = {
            "model": AI_MODEL,
            "max_tokens": 1024,
            "temperature": 0.1,
            "system": "你是资深的微信公众号运营专家。请仅返回合法的JSON字符串格式数据，包含'category'、'reason'和'summary'三个字段。category的值必须是'便民服务宣传'或'运营活动宣传'或'其他'。'reason'字段请用一句话说明分类理由，'summary'字段请对文章内容做一段30-50字的精简总结。",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
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
        
        response = requests.post(AI_ENDPOINT, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 200:
            res_json = response.json()
            # 这里的打印非常关键，请注意查看后台日志
            print_info(f"[AI-DEBUG] Raw Response: {json.dumps(res_json, ensure_ascii=False)}")
            
            ai_text = ""
            
            # 策略A：标准 Anthropic 格式提取 (content 列表)
            content_list = res_json.get("content", [])
            if isinstance(content_list, list):
                for block in content_list:
                    if isinstance(block, dict) and block.get("type") == "text":
                        ai_text = block.get("text", "")
                        break
                if not ai_text and content_list:
                    # 备选：如果只有内容块但没标 type
                    first_block = content_list[0]
                    if isinstance(first_block, dict):
                        ai_text = first_block.get("text", "")
                    elif isinstance(first_block, str):
                        ai_text = first_block

            # 策略B：备选提取 (某些代理或变体可能返回 choices)
            if not ai_text and "choices" in res_json:
                 choices = res_json.get("choices", [])
                 if choices:
                     ai_text = choices[0].get("message", {}).get("content", "")

            # 策略C：直接提取顶级 text 字段
            if not ai_text:
                ai_text = res_json.get("text", "")

            if not ai_text:
                error_msg = f"无法从响应中提取文本。结构: {json.dumps(res_json)[:200]}"
                print_error(f"[AI] {error_msg}")
                return {"category": "其他", "summary": error_msg}
            
            # 强力解析 JSON
            try:
                clean_text = ai_text.strip()
                if clean_text.startswith("```"):
                    match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_text, re.DOTALL)
                    if match:
                        clean_text = match.group(1).strip()
                
                # 处理可能的转义字符问题
                result = json.loads(clean_text)
                return {
                    "category": result.get("category", "其他"),
                    "reason": result.get("reason", ""),
                    "summary": result.get("summary", "")
                }
            except Exception as e:
                print_error(f"[AI] JSON 解析失败: {e}, 响应文本提示: {ai_text[:100]}")
                # 解析失败则返回原始内容的前 100 字
                return {"category": "其他", "summary": ai_text[:100]}
        else:
            print_error(f"[AI] 调用失败 {response.status_code}: {response.text}")
            return {"category": "其他", "summary": f"API 状态码: {response.status_code}"}
            
    except Exception as e:
        import traceback
        print_error(f"[AI] 系统错误: {str(e)}\n{traceback.format_exc()}")
        return {"category": "其他", "summary": f"系统错误: {str(e)}"}
