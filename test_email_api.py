#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试邮件API响应格式的脚本
"""

import sys
import os
import requests
import json
import time

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mail_service import MailApiClient
from utils.logger import setup_logger

def test_email_api_format():
    """测试邮件API的响应格式"""
    logger = setup_logger('test_email_api')
    logger.info("开始测试邮件API响应格式")
    
    # 创建邮件客户端
    client = MailApiClient()
    
    # 测试创建邮箱
    logger.info("测试创建邮箱...")
    email = client.create_email_address()
    
    if not email:
        logger.error("创建邮箱失败")
        return False
    
    logger.info(f"成功创建邮箱: {email}")
    
    # 测试获取邮件
    logger.info("测试获取邮件...")
    messages = client.get_messages(email)
    logger.info(f"获取到 {len(messages)} 封邮件")
    
    # 详细分析邮件格式
    for i, message in enumerate(messages):
        logger.info(f"邮件 {i+1}:")
        logger.info(f"  类型: {type(message)}")
        
        if isinstance(message, dict):
            logger.info(f"  键: {list(message.keys())}")
            for key, value in message.items():
                if key in ['from', 'subject', 'body', 'content']:
                    logger.info(f"  {key}: {value}")
                elif isinstance(value, str) and len(value) > 100:
                    logger.info(f"  {key}: {value[:100]}...")
                else:
                    logger.info(f"  {key}: {value}")
        else:
            logger.info(f"  内容: {message}")
    
    # 测试轮询功能
    logger.info("测试轮询功能（10秒）...")
    start_time = time.time()
    messages = client.poll_messages(email, max_wait_time=10)
    end_time = time.time()
    
    logger.info(f"轮询完成，耗时 {end_time - start_time:.1f} 秒")
    logger.info(f"轮询结果: {len(messages)} 封邮件")
    
    # 测试发送邮件（模拟注册）
    logger.info("模拟发送邮件到这个邮箱...")
    logger.info(f"请手动发送一封测试邮件到: {email}")
    logger.info("然后等待10秒，观察是否能收到邮件...")
    
    # 再次轮询
    time.sleep(10)
    messages = client.get_messages(email)
    logger.info(f"再次检查邮件: {len(messages)} 封邮件")
    
    logger.info("邮件API测试完成")
    return True

def test_raw_api():
    """直接测试原始API"""
    logger = setup_logger('test_raw_api')
    logger.info("开始测试原始API")
    
    base_url = "http://94.16.122.36:8000"
    
    # 测试 /new 端点
    logger.info("测试 /new 端点...")
    try:
        response = requests.get(f"{base_url}/new", timeout=10)
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"响应数据: {json.dumps(data, indent=2)}")
            email = data.get('email')
            
            if email:
                # 测试 /rec/{email} 端点
                logger.info(f"测试 /rec/{email} 端点...")
                response2 = requests.get(f"{base_url}/rec/{email}", timeout=10)
                logger.info(f"响应状态码: {response2.status_code}")
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    logger.info(f"邮件数据: {json.dumps(data2, indent=2)}")
                else:
                    logger.error(f"获取邮件失败: {response2.text}")
            else:
                logger.error("响应中没有email字段")
        else:
            logger.error(f"创建邮箱失败: {response.text}")
    except Exception as e:
        logger.error(f"测试原始API时发生错误: {e}")
    
    logger.info("原始API测试完成")

if __name__ == "__main__":
    print("邮件API测试脚本")
    print("=" * 50)
    
    # 测试原始API
    test_raw_api()
    
    print("\n" + "=" * 50)
    
    # 测试邮件服务
    test_email_api_format()