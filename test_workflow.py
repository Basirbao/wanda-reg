#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试注册流程的完整工作流
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.registration_service import RegistrationOrchestrator
from utils.logger import setup_logger

def test_registration_workflow():
    """测试注册工作流"""
    logger = setup_logger('test_workflow')
    logger.info("开始测试注册工作流")
    
    # 创建注册协调器
    orchestrator = RegistrationOrchestrator()
    
    try:
        # 执行注册（使用非headless模式以便观察）
        success = orchestrator.execute_registration(headless=False)  # 明确设置为False
        
        if success:
            logger.info("注册流程测试成功")
            print("注册流程测试成功！")
        else:
            logger.error("注册流程测试失败")
            print("注册流程测试失败，请查看日志了解详细信息")
    except Exception as e:
        logger.error(f"测试执行过程中发生错误: {str(e)}")
        print(f"测试执行失败: {str(e)}")
    finally:
        # 确保浏览器被关闭
        try:
            orchestrator.browser_service.close_browser()
        except Exception as close_error:
            logger.warning(f"关闭浏览器时发生错误: {str(close_error)}")

if __name__ == "__main__":
    test_registration_workflow()