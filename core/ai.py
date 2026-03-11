import os
import json
import requests
from core.config import cfg
from core.print import print_info, print_error, print_success, print_warning

MINIMAX_URL = "https://api.minimaxi.com/anthropic/v1/messages"

def get_system_prompt():
    """
    专门为 API 自动化调用优化的 System Prompt
    标签体系精简为「产品功能」「运营活动」「其他」三大类
    """
    return """
你现在是一位拥有10年经验的「资深政务便民APP产品与运营专家」。你精通数字政府建设、一网通办等业务逻辑。
你的任务是阅读我提供的【竞品公众号文章内容】，进行文章内容总结，判断文章属于哪个分类，并给出打标理由。

【分类体系】
文章只能属于以下三个分类中的一个：
1. 产品功能 —— 文章主要介绍或宣传APP的某个具体功能、服务上线、技术升级等内容
2. 运营活动 —— 文章主要介绍促销活动、补贴发放、抽奖互动、以旧换新、积分兑换等运营类内容
3. 其他 —— 不属于以上两类的内容（如纯政策通知、企业新闻、品牌宣传等）

【输出格式要求】
你必须且只能输出一个合法的 JSON 对象，不要包含任何 Markdown 标记（如 ```json ），不要包含任何额外的解释性文本。
JSON 结构必须严格如下所示：

{
  "basic_info": {
    "category": "产品功能 或 运营活动 或 其他",
    "core_theme": "一句话概括文章核心目的",
    "business_area": "涉及业务领域，如公积金、交通出行等",
    "article_summary": "文章的全面总结（100-150字左右），概括背景、核心动作和预期效果"
  },
  "tag_reason": "结合文章内容，说明为什么归入该分类的详细理由",
  "product_analysis": {
    "has_product_content": true,
    "function_name": "提炼政务/便民功能名称，无则填空",
    "pain_points": "解决的市民/企业痛点，无则填空",
    "interaction_flow": "简述APP上的操作路径，无则填空"
  },
  "operation_analysis": {
    "has_operation_content": true,
    "rules": "拆解市民参与路径和门槛，无则填空",
    "incentives": "具体的补贴形式/激励机制，无则填空",
    "strategy_purpose": "策略目的推测，无则填空"
  },
  "takeaways": [
    "借鉴与启发建议1",
    "借鉴与启发建议2"
  ]
}
"""

def analyze_article(title: str, content: str) -> dict:
    """
    调用 MiniMax 大模型接口，对文章进行结构化分析打标。
    分类为：产品功能、运营活动、其他。
    返回包含 category、summary 以及完整分析结果的字典。
    """
    if not title and not content:
        return {"category": "其他", "summary": "无内容无法判断", "ai_tags": ""}
        
    try:
        # 动态读取 API Key，支持热重载
        api_key = os.environ.get("MINIMAX_API_KEY") or cfg.get("minimax.api_key")
        if not api_key:
            print_error("[AI] 未检测到 MINIMAX_API_KEY。请在环境变量或 config.yaml (minimax.api_key) 中配置。")
            return {"category": "其他", "summary": "未配置AI大模型秘钥", "ai_tags": ""}
            
        # 裁剪文章长度防止 Token 超限（增大到4000字符提升分析质量）
        safe_content = content[:4000] if content else ""
        
        user_content = f"""
请分析以下竞品公众号文章：

【文章标题】{title}
【文章内容】{safe_content}
"""
        
        payload = {
            "model": "MiniMax-M2.5",
            "max_tokens": 4096,
            "system": get_system_prompt(),
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        print_info(f"[AI] 正在使用 MiniMax 给文章 '{title[:30]}' 打标...")
        response = requests.post(MINIMAX_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            res_json = response.json()
            
            content_blocks = res_json.get("content", [])
            ai_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    ai_text = block.get("text", "")
                    break
            
            if ai_text:
                
                # 兼容部分模型可能会包裹 Markdown 格式
                ai_text = ai_text.strip()
                if ai_text.startswith("```json"):
                    ai_text = ai_text[7:]
                elif ai_text.startswith("```"):
                    ai_text = ai_text[3:]
                if ai_text.endswith("```"):
                    ai_text = ai_text[:-3]
                ai_text = ai_text.strip()
                
                try:
                    result = json.loads(ai_text)
                    
                    # 提取分类（兼容旧字段）
                    valid_categories = ['产品功能', '运营活动', '其他']
                    basic_info = result.get('basic_info', {})
                    cat = basic_info.get('category', '其他')
                    if cat not in valid_categories:
                        cat = '其他'
                    
                    # 提取摘要（兼容旧字段）
                    summary = basic_info.get('article_summary', '') or basic_info.get('core_theme', '')
                    if not summary:
                        summary = result.get('tag_reason', 'AI分析完成')
                    
                    return {
                        "category": cat,
                        "summary": summary[:500],
                        "ai_tags": json.dumps(result, ensure_ascii=False)
                    }
                except json.JSONDecodeError:
                    print_error(f"[AI] JSON 解析失败, 清洗后的文本: {repr(ai_text)}")
                    print_error(f"[AI] 原始 API 返回: {json.dumps(res_json, ensure_ascii=False)}")
                    return {"category": "其他", "summary": "AI结果解析异常", "ai_tags": ""}
            else:
                print_error(f"[AI] API 返回内容异常或格式不符: {json.dumps(res_json, ensure_ascii=False)}")
                return {"category": "其他", "summary": "AI接口响应空内容", "ai_tags": ""}
        else:
            err_details = response.text
            try:
                err_json = response.json()
                if "error" in err_json:
                    err_details = err_json["error"].get("message", err_details)
            except Exception:
                pass
            print_error(f"[AI] API 调用失败, 状态码: {response.status_code}, 详情: {err_details}")
            return {"category": "其他", "summary": f"AI接口API异常: {response.status_code}", "ai_tags": ""}
    except Exception as e:
        print_error(f"[AI] 分析文章时发生系统错误: {str(e)}")
        return {"category": "其他", "summary": "调用大模型失败", "ai_tags": ""}
