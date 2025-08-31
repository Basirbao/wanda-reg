import sys
import os
import time

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.registration_service import RegistrationOrchestrator
from utils.logger import setup_logger
from config.settings import REGISTRATION_COUNT, HEADLESS_MODE

def main():
    """主程序入口"""
    logger = setup_logger('main')
    logger.info("Wandb.ai自动注册工具启动")
    logger.info(f"配置执行注册次数: {REGISTRATION_COUNT}")
    logger.info(f"浏览器模式: {'无头模式' if HEADLESS_MODE else '可见模式'}")
    
    # 如果使用无头模式，显示警告
    if HEADLESS_MODE:
        logger.warning("⚠️ 检测到无头模式，Wandb可能会阻止发送验证邮件")
        logger.warning("建议设置环境变量 HEADLESS_MODE=false 以使用可见模式")
        print("⚠️ 警告: 当前使用无头模式，可能会导致邮件接收失败")
        print("💡 建议: export HEADLESS_MODE=false 或在 .env 文件中设置 HEADLESS_MODE=false")
        print()
    
    # 创建注册协调器
    orchestrator = RegistrationOrchestrator()
    
    # 统计信息
    success_count = 0
    failure_count = 0
    
    try:
        # 循环执行指定次数的注册
        for i in range(REGISTRATION_COUNT):
            current_attempt = i + 1
            logger.info(f"开始第 {current_attempt}/{REGISTRATION_COUNT} 次注册")
            print(f"正在执行第 {current_attempt}/{REGISTRATION_COUNT} 次注册...")
            
            try:
                # 执行注册（使用非headless模式以便观察）
                print(HEADLESS_MODE)
                success = orchestrator.execute_registration(headless=HEADLESS_MODE)
                
                if success:
                    success_count += 1
                    logger.info(f"第 {current_attempt} 次注册成功")
                    print(f"第 {current_attempt} 次注册成功！账户信息已保存到auth.txt")
                else:
                    failure_count += 1
                    logger.error(f"第 {current_attempt} 次注册失败")
                    print(f"第 {current_attempt} 次注册失败，请查看日志了解详细信息")
                
                # 如果不是最后一次，等待一段时间再进行下一次注册
                if current_attempt < REGISTRATION_COUNT:
                    wait_time = 3  # 等待3秒
                    logger.info(f"等待 {wait_time} 秒后进行下一次注册...")
                    print(f"等待 {wait_time} 秒后进行下一次注册...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"第 {current_attempt} 次注册执行过程中发生错误: {str(e)}")
                print(f"第 {current_attempt} 次注册执行失败: {str(e)}")
                
                # 即使本次注册失败，也等待一段时间再继续下一次
                if current_attempt < REGISTRATION_COUNT:
                    wait_time = 3
                    logger.info(f"等待 {wait_time} 秒后继续下一次注册...")
                    print(f"等待 {wait_time} 秒后继续下一次注册...")
                    time.sleep(wait_time)
        
        # 输出最终统计信息
        logger.info(f"注册执行完成 - 总计: {REGISTRATION_COUNT}, 成功: {success_count}, 失败: {failure_count}")
        print(f"\n=== 注册执行完成 ===")
        print(f"总计: {REGISTRATION_COUNT} 次")
        print(f"成功: {success_count} 次")
        print(f"失败: {failure_count} 次")
        
    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {str(e)}")
        print(f"程序执行失败: {str(e)}")
    # 注意：不再需要在finally块中手动关闭浏览器，因为浏览器服务现在有更完善的资源管理

if __name__ == "__main__":
    main()