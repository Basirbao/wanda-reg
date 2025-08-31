import asyncio
import logging
from playwright.sync_api import sync_playwright
from config.settings import DEFAULT_TIMEOUT, PROXY_URL, parse_proxy_url

class BrowserAutomation:
    """浏览器自动化控制 - 统一同步实现"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._event_loop = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，确保资源正确释放"""
        self.close_browser()
    
    def start_browser(self, headless=True):
        """启动浏览器"""
        try:
            self.logger.info(f"开始启动浏览器，headless模式: {headless}")
            # 确保之前的所有资源都已正确清理
            self.close_browser()
            
            self.logger.info("正在启动Playwright...")
            self.playwright = sync_playwright().start()
            self.logger.info("Playwright启动成功")
            
            # 配置浏览器启动参数
            launch_args = ['--no-sandbox', '--disable-dev-shm-usage']
            self.logger.info(f"浏览器启动参数: {launch_args}")
            
            # 配置代理
            if PROXY_URL:
                proxy_config = parse_proxy_url(PROXY_URL)
                if proxy_config:
                    launch_args.extend([
                        f"--proxy-server={proxy_config['scheme']}://{proxy_config['hostname']}:{proxy_config['port']}"
                    ])
                    self.logger.info(f"已配置代理: {PROXY_URL}")
            
            self.logger.info("正在启动Chromium浏览器...")
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=launch_args
            )
            self.logger.info("Chromium浏览器启动成功")
            
            # 创建带代理认证的上下文（如果需要）
            if PROXY_URL and proxy_config and proxy_config['username']:
                self.logger.info("创建带代理认证的浏览器上下文...")
                self.context = self.browser.new_context(
                    proxy={
                        "server": f"{proxy_config['scheme']}://{proxy_config['hostname']}:{proxy_config['port']}",
                        "username": proxy_config['username'],
                        "password": proxy_config['password']
                    }
                )
            else:
                self.logger.info("创建标准浏览器上下文...")
                self.context = self.browser.new_context()
            
            self.logger.info("创建新页面...")
            self.page = self.context.new_page()
            self.logger.info("浏览器完全启动成功")
            return True
        except Exception as e:
            self.logger.error(f"启动浏览器时发生错误: {str(e)}")
            # 确保在启动失败时清理资源
            self.close_browser()
            return False
    
    def navigate_to_signup(self, url="https://wandb.ai/login?signup=true"):
        """导航到注册页面"""
        self.logger.info(f"开始导航到注册页面: {url}")
        if not self._check_page():
            return False
            
        try:
            self.logger.info("正在导航到目标URL...")
            # 增加超时时间到2分钟，使用domcontentloaded等待策略
            self.page.goto(url, timeout=120 * 1000, wait_until='domcontentloaded')
            self.logger.info(f"成功导航到 {url}")
            
            # 等待网络空闲状态
            self.logger.info("等待页面完全加载...")
            self.page.wait_for_load_state('networkidle', timeout=60 * 1000)
            self.logger.info("页面已完全加载")
            
            # 等待注册表单的邮件输入框出现
            self.logger.info("等待注册表单加载（查找邮箱输入框）...")
            self.page.wait_for_selector('input[type="email"]', timeout=60 * 1000)
            self.logger.info("注册表单已加载（邮箱输入框已出现）")
            return True
        except Exception as e:
            self.logger.error(f"导航到注册页面时发生错误: {str(e)}")
            # 记录当前页面URL和标题以便调试
            try:
                current_url = self.page.url
                page_title = self.page.title()
                self.logger.info(f"当前页面URL: {current_url}")
                self.logger.info(f"当前页面标题: {page_title}")
            except Exception as debug_error:
                self.logger.warning(f"获取调试信息时发生错误: {debug_error}")
            return False
    
    def fill_registration_form(self, email, password):
        """填写注册表单"""
        if not self._check_page():
            return False
            
        try:
            # 填写邮箱
            email_input = self.page.locator('input[type="email"]')
            email_input.fill(email)
            self.logger.info(f"已填写邮箱: {email}")
            
            # 填写密码
            password_input = self.page.locator('input[type="password"]').first
            password_input.fill(password)
            self.logger.info("已填写密码")
            
            # 点击注册按钮
            signup_button = self.page.locator('button:has-text("Sign up")').first
            signup_button.click()
            self.logger.info("已提交注册表单")
            
            return True
        except Exception as e:
            self.logger.error(f"填写注册表单时发生错误: {str(e)}")
            return False
    
    def open_verification_link(self, verification_url):
        """打开验证链接"""
        if not self._check_page():
            return False
            
        try:
            self.page.goto(verification_url, timeout=DEFAULT_TIMEOUT * 1000)
            self.logger.info(f"已打开验证链接: {verification_url}")
            
            # 等待页面加载完成
            self.page.wait_for_load_state('networkidle')
            return True
        except Exception as e:
            self.logger.error(f"打开验证链接时发生错误: {str(e)}")
            return False
    
    def click_show_email_button(self, email):
        """点击显示邮箱按钮
        
        Args:
            email (str): 临时邮箱地址，用于定位包含该邮箱文本的按钮
        """
        if not self._check_page():
            return False
            
        try:
            # 首先尝试主要定位器 - 查找具有特定类和文本的<a>标签
            main_selector = f'a.auth0-lock-social-button.auth0-lock-social-big-button:has-text("{email}")'
            self.logger.debug(f"尝试主要定位器: {main_selector}")
            
            # 等待按钮出现
            self.page.wait_for_selector(main_selector, timeout=DEFAULT_TIMEOUT * 1000)
            
            # 点击按钮
            self.page.click(main_selector)
            self.logger.info(f"成功点击显示邮箱按钮(主要定位器): {email}")
            
            # 等待页面加载完成
            self.page.wait_for_load_state('networkidle')
            return True
        except Exception as main_error:
            self.logger.warning(f"使用主要定位器点击显示邮箱按钮失败: {main_error}")
            try:
                # 回退到基于类的选择器
                fallback_selector = f'a.auth0-lock-social-button.auth0-lock-social-big-button:has(div.auth0-lock-social-button-text:has-text("{email}"))'
                self.logger.debug(f"尝试备用定位器: {fallback_selector}")
                
                # 等待按钮出现
                self.page.wait_for_selector(fallback_selector, timeout=DEFAULT_TIMEOUT * 1000)
                
                # 点击按钮
                self.page.click(fallback_selector)
                self.logger.info(f"成功点击显示邮箱按钮(备用定位器): {email}")
                
                # 等待页面加载完成
                self.page.wait_for_load_state('networkidle')
                return True
            except Exception as fallback_error:
                self.logger.error(f"使用备用定位器点击显示邮箱按钮也失败: {fallback_error}")
                # 记录截图以便调试
                try:
                    screenshot_path = f"error_screenshot_{email.split('@')[0]}.png"
                    self.page.screenshot(path=screenshot_path)
                    self.logger.info(f"错误截图已保存至: {screenshot_path}")
                except Exception as screenshot_error:
                    self.logger.warning(f"保存错误截图时发生错误: {screenshot_error}")
                return False
    
    def handle_post_verification_navigation(self):
        """处理验证后页面导航"""
        if not self._check_page():
            return False
            
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 可以在这里添加后续页面操作的逻辑
            self.logger.info("验证后页面处理完成")
            return True
        except Exception as e:
            self.logger.warning(f"处理验证后页面导航时出现问题: {e}")
            return False
    
    def complete_registration_process(self, email, password, verification_url):
        """执行完整注册流程"""
        try:
            # 1. 填写并提交注册表单
            if not self.fill_registration_form(email, password):
                return False
            
            # 2. 打开验证链接
            if not self.open_verification_link(verification_url):
                return False
            
            # 3. 点击显示邮箱按钮
            if not self.click_show_email_button(email):
                # 不抛出异常，记录错误并继续执行
                self.logger.warning("点击显示邮箱按钮失败，但继续执行后续步骤")
            
            # 4. 处理验证后的页面导航
            if not self.handle_post_verification_navigation():
                return False
            
            self.logger.info("完整注册流程执行成功")
            return True
        except Exception as e:
            self.logger.error(f"注册流程执行失败: {e}")
            return False
    
    def close_browser(self):
        """关闭浏览器实例"""
        try:
            # 先检查浏览器是否存在且已连接
            if self.browser and self.browser.is_connected():
                try:
                    self.browser.close()
                    self.logger.info("浏览器已关闭")
                except Exception as e:
                    self.logger.warning(f"关闭浏览器时发生错误: {e}")
            else:
                if self.browser:
                    self.logger.warning("浏览器已经断开连接或未初始化")
                else:
                    self.logger.debug("浏览器未初始化")
        except Exception as e:
            self.logger.error(f"关闭浏览器时出错: {e}")
        finally:
            # 清理资源
            self.browser = None
            self.context = None
            self.page = None
            
            # 关闭playwright实例
            try:
                if self.playwright:
                    self.playwright.stop()
                    self.logger.info("Playwright实例已停止")
            except Exception as e:
                self.logger.error(f"停止Playwright实例时出错: {e}")
            finally:
                self.playwright = None
    
    def open_verification_link_in_new_tab(self, verification_url):
        """在新标签页中打开验证链接"""
        if not self._check_context():
            return False
            
        try:
            # 保存当前页面引用，以便在需要时回退
            original_page = self.page
            
            # 创建新页面
            new_page = self.context.new_page()
            
            try:
                # 在新页面中打开验证链接
                new_page.goto(verification_url, timeout=DEFAULT_TIMEOUT * 1000)
                self.logger.info(f"已在新标签页中打开验证链接: {verification_url}")
                
                # 等待页面加载完成
                new_page.wait_for_load_state('networkidle')
                
                # 将新页面设置为当前页面，以便后续操作可以正常进行
                self.page = new_page
                
                # 尝试关闭原始页面以释放资源
                try:
                    if original_page and not original_page.is_closed():
                        original_page.close()
                except Exception as close_error:
                    self.logger.warning(f"关闭原始页面时发生错误: {str(close_error)}")
                
                return True
            except Exception as goto_error:
                # 如果导航失败，尝试关闭新页面
                try:
                    if new_page and not new_page.is_closed():
                        new_page.close()
                except Exception as close_error:
                    self.logger.warning(f"关闭新页面时发生错误: {str(close_error)}")
                
                self.logger.error(f"在新标签页中打开验证链接时发生错误: {str(goto_error)}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建新页面时发生错误: {str(e)}")
            return False
    
    def _check_page(self):
        """检查页面是否可用"""
        if not self.page:
            self.logger.error("页面未初始化")
            return False
        return True
    
    def _check_context(self):
        """检查上下文是否可用"""
        if not self.context:
            self.logger.error("浏览器上下文未初始化")
            return False
        return True
