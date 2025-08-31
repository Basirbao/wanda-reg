#!/usr/bin/env python3

"""
测试新的邮箱API服务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mail_service import MailTMApiClient
from utils.logger import setup_logger

def test_mail_service():
    logger = setup_logger('mail_test')
    logger.info("开始测试邮箱API服务")
    
    mail_client = MailTMApiClient()
    
    try:
        logger.info("测试1: 获取可用域名")
        domains = mail_client._get_domains()
        if domains:
            logger.info(f"✅ 成功获取 {len(domains)} 个域名")
            for domain in domains[:3]:  # 只显示前3个
                logger.info(f"  - {domain.get('domainName', 'N/A')}")
        else:
            logger.error("❌ 获取域名失败")
            return
        
        logger.info("测试2: 创建临时邮箱账户")
        import string
        import random
        # 生成随机用户名
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = 'TestPass123!'
        
        account = mail_client.create_account(username, password)
        if account:
            email = account.get('address')
            logger.info(f"✅ 成功创建邮箱: {email}")
            
            logger.info("测试3: 获取访问令牌")
            token = mail_client.get_token(email, password)
            if token:
                logger.info("✅ 成功获取访问令牌")
                
                logger.info("测试4: 检查邮件")
                messages = mail_client.get_messages()
                logger.info(f"get_messages() 返回: {messages}")
                if messages and isinstance(messages, dict) and 'hydra:member' in messages:
                    member_data = messages['hydra:member'] or []  # 处理 None 的情况
                    message_count = len(member_data)
                    logger.info(f"✅ 成功检查邮件，当前邮件数: {message_count}")
                elif messages:
                    logger.info(f"✅ 成功检查邮件，但响应格式异常: {type(messages)}")
                else:
                    logger.info("✅ 成功检查邮件，当前邮件数: 0")
            else:
                logger.error("❌ 获取访问令牌失败")
        else:
            logger.error("❌ 创建邮箱账户失败")
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")

if __name__ == "__main__":
    test_mail_service()