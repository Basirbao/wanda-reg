#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试无头模式vs可见模式的邮件获取
"""

import sys
import os
import time

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mail_service import MailApiClient
from services.browser_service import BrowserAutomation
from utils.logger import setup_logger

def test_headless_vs_visible():
    """测试无头模式和可见模式的区别"""
    logger = setup_logger('test_headless')
    
    print("测试无头模式 vs 可见模式的邮件获取")
    print("=" * 50)
    
    # 创建邮件客户端
    mail_client = MailApiClient()
    
    # 创建临时邮箱
    email = mail_client.create_email_address()
    print(f"创建邮箱: {email}")
    
    # 测试无头模式
    print("\n1. 测试无头模式...")
    browser_headless = BrowserAutomation()
    
    try:
        print("启动无头浏览器...")
        start_time = time.time()
        success = browser_headless.start_browser(headless=True)
        if success:
            print(f"无头浏览器启动成功，耗时: {time.time() - start_time:.1f}秒")
            
            # 导航到wandb注册页面
            print("导航到wandb注册页面...")
            nav_start = time.time()
            if browser_headless.navigate_to_signup():
                print(f"导航成功，耗时: {time.time() - nav_start:.1f}秒")
                
                # 填写注册表单
                print("填写注册表单...")
                form_start = time.time()
                password = "TestPassword123!"
                if browser_headless.fill_registration_form(email, password):
                    print(f"表单填写成功，耗时: {time.time() - form_start:.1f}秒")
                    
                    # 等待一段时间，然后检查邮件
                    print("等待10秒后检查邮件...")
                    time.sleep(10)
                    
                    messages = mail_client.get_messages(email)
                    print(f"无头模式下收到邮件数量: {len(messages)}")
                    
                    if messages:
                        print("✅ 无头模式成功收到邮件")
                    else:
                        print("❌ 无头模式未收到邮件")
                else:
                    print("❌ 表单填写失败")
            else:
                print("❌ 导航失败")
        else:
            print("❌ 无头浏览器启动失败")
            
    except Exception as e:
        print(f"❌ 无头模式测试出错: {e}")
    finally:
        try:
            browser_headless.close_browser()
            print("无头浏览器已关闭")
        except:
            pass
    
    # 测试可见模式
    print("\n2. 测试可见模式...")
    browser_visible = BrowserAutomation()
    
    try:
        print("启动可见浏览器...")
        start_time = time.time()
        success = browser_visible.start_browser(headless=False)
        if success:
            print(f"可见浏览器启动成功，耗时: {time.time() - start_time:.1f}秒")
            
            # 导航到wandb注册页面
            print("导航到wandb注册页面...")
            nav_start = time.time()
            if browser_visible.navigate_to_signup():
                print(f"导航成功，耗时: {time.time() - nav_start:.1f}秒")
                
                # 填写注册表单
                print("填写注册表单...")
                form_start = time.time()
                password = "TestPassword123!"
                if browser_visible.fill_registration_form(email, password):
                    print(f"表单填写成功，耗时: {time.time() - form_start:.1f}秒")
                    
                    # 等待一段时间，然后检查邮件
                    print("等待10秒后检查邮件...")
                    time.sleep(10)
                    
                    messages = mail_client.get_messages(email)
                    print(f"可见模式下收到邮件数量: {len(messages)}")
                    
                    if messages:
                        print("✅ 可见模式成功收到邮件")
                    else:
                        print("❌ 可见模式未收到邮件")
                else:
                    print("❌ 表单填写失败")
            else:
                print("❌ 导航失败")
        else:
            print("❌ 可见浏览器启动失败")
            
    except Exception as e:
        print(f"❌ 可见模式测试出错: {e}")
    finally:
        try:
            browser_visible.close_browser()
            print("可见浏览器已关闭")
        except:
            pass
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_headless_vs_visible()