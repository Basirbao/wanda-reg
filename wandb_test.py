#!/usr/bin/env python3

"""
测试wandb注册页面导航
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.browser_service import BrowserAutomation
from utils.logger import setup_logger

def test_wandb_signup():
    logger = setup_logger('wandb_test')
    logger.info("开始wandb注册页面测试")
    
    browser_service = BrowserAutomation()
    
    try:
        logger.info("启动浏览器...")
        if not browser_service.start_browser(headless=False):
            logger.error("浏览器启动失败")
            return
        
        logger.info("导航到wandb注册页面...")
        if browser_service.navigate_to_signup():
            logger.info("✅ 成功导航到注册页面")
            
            # 获取当前页面信息
            current_url = browser_service.page.url
            page_title = browser_service.page.title()
            logger.info(f"当前URL: {current_url}")
            logger.info(f"页面标题: {page_title}")
            
            # 检查是否有邮箱输入框
            email_inputs = browser_service.page.locator('input[type="email"]').count()
            logger.info(f"找到 {email_inputs} 个邮箱输入框")
            
        else:
            logger.error("❌ 导航到注册页面失败")
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
    finally:
        try:
            browser_service.close_browser()
            logger.info("浏览器已关闭")
        except Exception as close_error:
            logger.warning(f"关闭浏览器时发生错误: {str(close_error)}")

if __name__ == "__main__":
    test_wandb_signup()