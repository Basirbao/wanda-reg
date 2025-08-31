import time
import logging
import re
from services.mail_service import MailApiClient
from services.browser_service import BrowserAutomation
from utils.password_generator import generate_secure_password
from utils.logger import setup_logger
from config.settings import DEFAULT_RETRY_ATTEMPTS, FULL_NAME, COMPANY_NAME

class RegistrationOrchestrator:
    """注册流程协调器"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.mail_client = MailApiClient()
        self.browser_service = BrowserAutomation()
    
    def execute_registration(self, headless=True):
        """执行完整注册流程"""
        # 如果使用无头模式，显示警告
        if headless:
            self.logger.warning("⚠️ 检测到无头模式，Wandb可能会阻止发送验证邮件")
            self.logger.warning("建议使用可见模式 (headless=False) 以获得最佳效果")
        
        for attempt in range(DEFAULT_RETRY_ATTEMPTS):
            try:
                self.logger.info(f"🔄 开始第 {attempt + 1}/{DEFAULT_RETRY_ATTEMPTS} 次注册尝试")
                
                # 创建临时邮箱地址
                email = self.mail_client.create_email_address()
                
                if not email:
                    self.logger.error("创建临时邮箱失败")
                    time.sleep(10)  # 等待10秒
                    continue
                
                self.logger.info(f"📧 生成临时邮箱: {email}")
                
                # 生成随机密码
                password = generate_secure_password()
                
                # 启动浏览器
                self.logger.info("正在启动浏览器...")
                if not self.browser_service.start_browser(headless=headless):
                    self.logger.error("启动浏览器失败")
                    time.sleep(10)  # 等待10秒
                    continue
                
                # 导航到注册页面并填写表单
                if not self.browser_service.navigate_to_signup():
                    self.logger.error("导航到注册页面失败")
                    self.browser_service.close_browser()
                    time.sleep(10)  # 等待10秒
                    continue
                
                if not self.browser_service.fill_registration_form(email, password):
                    self.logger.error("填写注册表单失败")
                    self.browser_service.close_browser()
                    time.sleep(10)  # 等待10秒
                    continue
                
                # 等待注册完成
                # 使用改进的检查方式
                if hasattr(self.browser_service, 'page') and self.browser_service.page:
                    self.browser_service.page.wait_for_load_state('networkidle')
                
                # 获取验证链接
                self.logger.info("📬 等待验证邮件...")
                self.logger.info(f"📧 使用邮箱: {email}")
                self.logger.info(f"🔐 使用密码: {password}")
                verification_link = self.mail_client.get_verification_link(email)
                
                if verification_link:
                    self.logger.info("✅ 验证链接:" + verification_link)
                else:
                    self.logger.info("❌ 未获取到验证链接")
                
                if not verification_link:
                    self.logger.warning("⚠️ 验证邮件获取失败，将尝试生成新邮箱重试")
                    self.browser_service.close_browser()
                    time.sleep(3)  # 短暂等待后重试
                    continue  # 重新开始循环，生成新的邮箱账户
                
                self.browser_service.close_browser()
                # 启动浏览器
                if not self.browser_service.start_browser(headless=headless):
                    self.logger.error("启动浏览器失败")
                    time.sleep(10)  # 等待10秒
                    continue
                
                
                # 打开验证链接
                if not self.browser_service.open_verification_link_in_new_tab(verification_link):
                    self.logger.error("打开验证链接失败")
                    self.browser_service.close_browser()
                    time.sleep(10)  # 等待10秒
                    continue
                
                # 完成注册后的步骤
                if self.complete_registration_process(email, password, verification_link):

                    # 提取API密钥
                    api_key = self.extract_api_key()
                    
                    # 保存账户信息和API密钥
                    self.save_account_info(email, password, api_key)
                    
                    self.logger.info(f"注册成功: {email}")
                    # 确保浏览器正确关闭
                    try:
                        self.browser_service.close_browser()
                    except Exception as close_error:
                        self.logger.warning(f"关闭浏览器时发生错误: {str(close_error)}")
                    return True
                else:
                    self.logger.error("完成注册流程失败")
                    # 确保浏览器正确关闭
                    try:
                        self.browser_service.close_browser()
                    except Exception as close_error:
                        self.logger.warning(f"关闭浏览器时发生错误: {str(close_error)}")
                    return False
                
            except Exception as e:
                self.logger.error(f"注册过程中发生错误: {str(e)}")
                try:
                    self.browser_service.close_browser()
                except Exception as close_error:
                    self.logger.warning(f"关闭浏览器时发生错误: {str(close_error)}")
                time.sleep(10)  # 增加延迟
                continue
        
        self.logger.error("所有注册尝试均失败")
        return False
    
    def complete_registration_process(self, email, password, verification_url):
        """完成注册后的所有步骤 - 协调方法
        
        Args:
            email (str): 临时邮箱地址，用于定位显示邮箱按钮
            password (str): 账户密码
            verification_url (str): 验证链接
        """
        try:
            print(email)
            print(f"验证链接: {verification_url}")  # 使用verification_url参数
            self.browser_service.page.wait_for_load_state('networkidle')

            # 在输入框中填写email内容和在密码框中输入password内容，输入完成后，点击Log in按钮
            try:
                self.logger.info("等待页面加载...")
                self.browser_service.page.wait_for_load_state('networkidle')
                self.browser_service.page.wait_for_selector('input[type="email"]', timeout=30 * 1000)

                # 查找并填写邮箱输入框
                email_input = self.browser_service.page.locator('input[type="email"]')
                if email_input.count() > 0:
                    email_input.fill(email)
                    self.logger.info(f"已填写邮箱: {email}")
                else:
                    self.logger.warning("未找到邮箱输入框")
                
                # 查找并填写密码输入框
                password_input = self.browser_service.page.locator('input[type="password"]')
                if password_input.count() > 0:
                    password_input.fill(password)
                    self.logger.info("已填写密码")
                else:
                    self.logger.warning("未找到密码输入框")
                
                # 点击Log in按钮
                login_button = self.browser_service.page.locator('button:has-text("Log in")')
                if login_button.count() > 0:
                    login_button.first.click()
                    self.logger.info("已点击Log in按钮")
                    self.browser_service.page.wait_for_load_state('networkidle')
                else:
                    self.logger.warning("未找到Log in按钮")
            
            except Exception as e:
                self.logger.error(f"登录过程中发生错误: {str(e)}")
                # 即使失败也继续尝试后续步骤
            
            time.sleep(5)
            # 填写用户详情
            self._fill_user_details()
            
            # 处理组织设置
            self._handle_organization_setup()
            # time.sleep(4)
            
            # 处理产品选择
            self._handle_product_selection()
            time.sleep(3)
            
            # 切换到学习模式
            self._changetostudy(email)
            return True
        except Exception as e:
            self.logger.error(f"完成注册流程时发生错误: {str(e)}")
            return False
    
    def _fill_user_details(self):
        """填写用户详情信息"""
        # 检查页面是否可用
        if not hasattr(self.browser_service, 'page') or not self.browser_service.page:
            self.logger.error("浏览器页面未初始化，无法填写用户详情")
            return
            
        try:
            # 等待页面加载
            self.browser_service.page.wait_for_load_state('networkidle')
            # time.sleep(15)
            self.browser_service.page.wait_for_selector('input[data-test="name-input"]', timeout=30 * 1000)
            # 填写Full name和Company or Institution
            full_name_input = self.browser_service.page.locator('input[data-test="name-input"]')
            if full_name_input.count() > 0:
                full_name_input.fill(FULL_NAME)
                self.logger.info(f"已填写Full name: {FULL_NAME}")
            
            company_input = self.browser_service.page.locator('input[aria-describedby="react-select-2-placeholder"]')
            if company_input.count() > 0:
                company_input.fill(COMPANY_NAME)
                time.sleep(5)
                self.logger.info(f"已填写Company or Institution: {COMPANY_NAME}")

            time.sleep(8)
            # 勾选复选框
            # 获取所有匹配的定位器
            all_checkboxes = self.browser_service.page.locator('button[role="checkbox"]').all()
            # 遍历并点击每一个
            for checkbox in all_checkboxes:
                checkbox.click()
            self.logger.info("已勾选Terms of Service and Privacy Policy")
            
            # 点击Continue按钮
            continue_button = self.browser_service.page.locator('button:has-text("Continue")').first
            if continue_button.count() > 0:
                continue_button.click()
                self.logger.info("已点击Continue按钮")
            
            # # 等待页面跳转
            # self.browser_service.page.wait_for_load_state('networkidle')
        except Exception as e:
            self.logger.error(f"填写用户详情时发生错误: {str(e)}")
            # 不抛出异常，继续执行
    
    def _handle_organization_setup(self):
        """处理组织设置"""
        # 检查页面是否可用
        if not hasattr(self.browser_service, 'page') or not self.browser_service.page:
            self.logger.error("浏览器页面未初始化，无法处理组织设置")
            return
            
        try:
            # # 等待页面加载
            # self.browser_service.page.wait_for_load_state('networkidle')
            
            # 在Create your organization页面点击Continue按钮
            create_org_continue_button = self.browser_service.page.locator('button:has-text("Continue")').first
            if create_org_continue_button.count() > 0:
                create_org_continue_button.click()
                self.logger.info("已在Create your organization页面点击Continue按钮")
            
            # 等待页面跳转
            # self.browser_service.page.wait_for_load_state('networkidle')
        except Exception as e:
            self.logger.error(f"处理组织设置时发生错误: {str(e)}")
            # 不抛出异常，继续执行
    
    def _handle_product_selection(self):
        """处理产品选择"""
        # 检查页面是否可用
        if not hasattr(self.browser_service, 'page') or not self.browser_service.page:
            self.logger.error("浏览器页面未初始化，无法处理产品选择")
            return
            
        try:
            # 等待页面加载
            # self.browser_service.page.wait_for_load_state('networkidle')
            
            time.sleep(4)
            self.logger.info("开始处理产品选择")
            self.browser_service.page.wait_for_selector('button[value="weave"]', timeout=30 * 1000)
            
            # 在What do you want to try first?页面点击Weave选项
            weave_option = self.browser_service.page.locator('button[value="weave"]') #button[role="checkbox"]
            if weave_option.count() > 0:
                weave_option.click()
                self.logger.info("已点击Weave选项")
                
                # 点击Continue按钮
                weave_continue_button = self.browser_service.page.locator('button:has-text("Continue")').first
                if weave_continue_button.count() > 0:
                    weave_continue_button.click()
                    self.logger.info("已在Weave页面点击Continue按钮")
                
                # 等待页面跳转
                # self.browser_service.page.wait_for_load_state('networkidle')
            else:
                self.logger.info("Can not find button")
        except Exception as e:
            self.logger.error(f"处理产品选择时发生错误: {str(e)}")
            # 不抛出异常，继续执行
    def _changetostudy(self, email):
        """改为学习模式"""
        # 检查页面是否可用
        if not hasattr(self.browser_service, 'page') or not self.browser_service.page:
            self.logger.error("浏览器页面未初始化，无法提取API密钥")
            return None
            
        try:
            # 直接跳转到API密钥页面
            time.sleep(10)
            self.browser_service.page.goto("https://wandb.ai/academic_application", timeout=30 * 1000)
            self.logger.info("已跳转到学习页面")
            
            # 等待页面内容加载，使用data-test属性精确定位
            self.logger.info("等待元素加载...")
            study_container = self.browser_service.page.wait_for_selector('div:has-text("Select role")', timeout=30 * 1000)
            #react-select-2-placeholder
            if not study_container:
                self.logger.error("未找到data-test='Select role'的元素")
                return None
            
            # self.browser_service.page.click('#react-select-2-placeholder')
            # 选择角色（react-select-2）：点击占位 -> 等 aria-expanded=true -> 等 listbox -> 点第一个选项
            try:
                self.logger.info("[角色] 点击 placeholder #react-select-2-placeholder")
                ph = self.browser_service.page.locator('#react-select-2-placeholder')
                ph.scroll_into_view_if_needed()
                ph.click(timeout=3000)

                # 1) 等 aria-expanded=true（用 combobox input 判断是否展开）
                combo = self.browser_service.page.locator('#react-select-2-input')
                self.logger.info("[角色] 等待 aria-expanded=true")
                self.browser_service.page.wait_for_function(
                    """el => el && el.getAttribute('aria-expanded') === 'true'""",
                    arg=combo,
                    timeout=5000
                )

                # 2) 取出 listbox id（更稳，不写死）
                listbox_id = combo.get_attribute('aria-controls') or combo.get_attribute('aria-owns')
                self.logger.info(f"[角色] listbox id = {listbox_id}")

                # 3) 等 listbox 挂载并可见（react-select 可能挂在 body portal）
                listbox_sel = f"#{listbox_id}" if listbox_id else '[role="listbox"]'
                self.logger.info(f"[角色] 等待 listbox 出现: {listbox_sel}")
                listbox = self.browser_service.page.locator(listbox_sel)
                listbox.wait_for(state='visible', timeout=5000)

                # 4) 等选项出现（优先用 react-select 的 option id 前缀）
                option_query = f"{listbox_sel} [id^='react-select-2-option-'], {listbox_sel} [role='option']"
                self.logger.info(f"[角色] 等待选项: {option_query}")
                options = self.browser_service.page.locator(option_query)
                options.first.wait_for(state='visible', timeout=5000)

                count = options.count()
                self.logger.info(f"[角色] 找到 {count} 个选项，点击第一个")
                options.first.click(timeout=3000)

                # 5) 校验已经选择（单值展示）
                chosen = self.browser_service.page.locator('div.css-1dimb5e-singleValue').first
                if chosen.count() > 0:
                    text = chosen.inner_text().strip()
                    self.logger.info(f"[角色] 选择完成: {text}")
                else:
                    self.logger.info("[角色] 未读到单值展示，可能 UI 风格不同")

            except Exception as e:
                self.logger.warning(f"[角色] 常规选择失败: {e}")
                # 兜底：聚焦 input，键盘打开并选第一个
                try:
                    self.logger.info("[角色-fallback] 聚焦 input + 键盘 ArrowDown/Enter")
                    combo = self.browser_service.page.locator('#react-select-2-input')
                    combo.focus()
                    self.browser_service.page.keyboard.press('Enter')
                    self.browser_service.page.keyboard.press('ArrowDown')
                    self.browser_service.page.keyboard.press('Enter')
                    self.logger.info("[角色-fallback] 键盘选择已尝试")
                except Exception as e2:
                    self.logger.error(f"[角色-fallback] 失败: {e2}")
            time.sleep(3)
            # 勾选复选框
            # 获取所有匹配的定位器
            self.browser_service.page.wait_for_selector('div[data-test="checkbox"]', timeout=30 * 1000)
            all_checkboxes = self.browser_service.page.locator('button[role="checkbox"]').all()
            # 遍历并点击每一个
            for checkbox in all_checkboxes:
                checkbox.click()
            self.logger.info("已勾选 checking box")
            
            #选择邮件选项
            try:
                self.logger.info("开始选择邮件")
                
                # 方法1：使用更精确的选择器定位邮件控件
                email_control = self.browser_service.page.locator('div.css-163qdeh:has(#react-select-3-placeholder)')
                if email_control.count() > 0:
                    email_control.click()
                    self.logger.info("点击了邮件控件")
                    time.sleep(2)
                    
                    # 检查下拉框是否展开
                    email_input = self.browser_service.page.locator('#react-select-3-input')
                    is_expanded = email_input.get_attribute('aria-expanded') == 'true'
                    
                    if is_expanded:
                        self.logger.info("下拉框已展开")
                        
                        # 获取aria-controls属性来找到对应的选项列表
                        listbox_id = email_input.get_attribute('aria-controls')
                        self.logger.info(f"邮件选项列表ID: {listbox_id}")
                        
                        if listbox_id:
                            # 等待选项列表出现
                            options_selector = f"#{listbox_id} [role='option']"
                            self.browser_service.page.wait_for_selector(options_selector, timeout=5000)
                            options = self.browser_service.page.locator(options_selector)
                            
                            if options.count() > 0:
                                # 查找包含邮件地址的选项
                                for i in range(options.count()):
                                    option = options.nth(i)
                                    text = option.inner_text()
                                    self.logger.info(f"选项 {i+1}: {text}")
                                    
                                    if '@' in text:
                                        self.logger.info(f"找到邮件选项: {text}")
                                        option.click()
                                        self.logger.info("已选择邮件")
                                        break
                                else:
                                    # 如果没找到包含@的，选择第一个选项
                                    options.first.click()
                                    self.logger.info("已选择第一个选项")
                            else:
                                self.logger.warning("未找到任何选项")
                        else:
                            # 备用方法：查找所有可见的选项
                            all_options = self.browser_service.page.locator('[role="option"]:visible')
                            if all_options.count() > 0:
                                for i in range(all_options.count()):
                                    option = all_options.nth(i)
                                    text = option.inner_text()
                                    if '@' in text:
                                        self.logger.info(f"找到邮件选项: {text}")
                                        option.click()
                                        self.logger.info("已选择邮件")
                                        break
                                else:
                                    all_options.first.click()
                                    self.logger.info("已选择第一个可见选项")
                    else:
                        self.logger.warning("下拉框未展开，尝试备用方法")
                        # 备用方法：使用键盘操作
                        email_input.focus()
                        self.browser_service.page.keyboard.press('Space')
                        time.sleep(1)
                        
                        # 再次检查是否展开
                        is_expanded = email_input.get_attribute('aria-expanded') == 'true'
                        if is_expanded:
                            # 使用键盘选择第一个选项
                            self.browser_service.page.keyboard.press('ArrowDown')
                            time.sleep(0.5)
                            self.browser_service.page.keyboard.press('Enter')
                            self.logger.info("通过键盘选择了邮件")
                else:
                    self.logger.warning("未找到邮件控件，尝试备用方法")
                    # 备用方法：直接点击placeholder
                    email_placeholder = self.browser_service.page.locator('#react-select-3-placeholder')
                    if email_placeholder.count() > 0:
                        email_placeholder.click()
                        self.logger.info("点击了邮件placeholder")
                        time.sleep(2)
                        
                        # 尝试选择第一个选项
                        all_options = self.browser_service.page.locator('[role="option"]:visible')
                        if all_options.count() > 0:
                            for i in range(all_options.count()):
                                option = all_options.nth(i)
                                text = option.inner_text()
                                if '@' in text:
                                    self.logger.info(f"找到邮件选项: {text}")
                                    option.click()
                                    self.logger.info("已选择邮件")
                                    break
                            else:
                                all_options.first.click()
                                self.logger.info("已选择第一个可见选项")
                            
            except Exception as e:
                self.logger.warning(f"选择邮件失败: {e}")
                # 尝试备用方案：直接输入
                try:
                    self.logger.info("尝试备用方案：直接输入邮件地址")
                    email_input = self.browser_service.page.locator('#react-select-3-input')
                    email_input.focus()
                    email_input.type(email)  # 使用当前注册的邮箱地址
                    time.sleep(1)
                    email_input.press('Enter')
                    self.logger.info("已输入邮件地址")
                except Exception as e2:
                    self.logger.error(f"备用方案也失败: {e2}")
            
            school_name = "ads"
            self.logger.info(f"输入学校名称: {school_name}")
            
            # 点击学校选择控件
            school_control = self.browser_service.page.locator('div.css-1ivaios-control')
            if school_control.count() > 0:
                school_control.click()
                self.logger.info("已点击学校选择控件")
                time.sleep(1)
                
                # 输入学校名称
                school_input = self.browser_service.page.locator('#react-select-4-input')
                if school_input.count() > 0:
                    school_input.fill(school_name)
                    self.logger.info(f"已输入学校名称: {school_name}")
                    time.sleep(2)  # 等待搜索结果加载
                    
                    # 等待并选择最后一个选项
                    try:
                        # 等待选项出现
                        options = self.browser_service.page.locator('[role="option"]')
                        if options.count() > 0:
                            # 选择最后一个选项（通常是最佳匹配）
                            options.last.click()
                            self.logger.info("已选择最后一个学校选项")
                        else:
                            # 如果没有选项，按Enter确认
                            school_input.press('Enter')
                            self.logger.info("已按Enter确认学校名称")
                    except Exception as e:
                        self.logger.warning(f"选择学校选项失败: {e}")
                        # 备用方案：按Enter确认
                        school_input.press('Enter')
                        self.logger.info("已按Enter确认学校名称")
                else:
                    self.logger.warning("未找到学校输入框")
            else:
                self.logger.warning("未找到学校选择控件")
             
            # 准备理由文本（确保超过30个字）
            reason_text = "I am applying for academic access to use Weights & Biases for my machine learning research projects and coursework at university."

            # 定位并填写 textarea
            self.logger.info("填写申请理由...")
            reason_textarea = self.browser_service.page.wait_for_selector('textarea.night-aware', timeout=5000)
            reason_textarea.fill(reason_text)

            # 点击年份选择下拉框
            # 选择毕业年份
            try:
                # 方法1: 使用特定的 react-select-5 ID
                year_control = self.browser_service.page.locator('div.css-1fftuef-control:has(#react-select-5-placeholder)')
                if year_control.count() > 0:
                    year_control.click()
                    time.sleep(0.5)
                    
                    # 获取对应的 listbox ID
                    year_input = self.browser_service.page.locator('#react-select-5-input')
                    aria_controls = year_input.get_attribute('aria-controls')
                    
                    if aria_controls:
                        # 在特定的 listbox 中查找选项
                        options = self.browser_service.page.locator(f'#{aria_controls} [role="option"]')
                        self.browser_service.page.wait_for_selector(f'#{aria_controls} [role="option"]', timeout=3000)
                        
                        if options.count() > 0:
                            # 选择最后一个选项（通常是最近的年份）
                            options.last.click()
                            self.logger.info("已选择毕业年份")
                    else:
                        # 备用方法：直接查找可见的选项
                        self.browser_service.page.wait_for_selector('[role="option"]:visible', timeout=3000)
                        visible_options = self.browser_service.page.locator('[role="option"]:visible')
                        
                        # 查找包含年份的选项（4位数字）
                        for i in range(visible_options.count()):
                            text = visible_options.nth(i).text_content()
                            if text and text.strip().isdigit() and len(text.strip()) == 4:
                                visible_options.nth(i).click()
                                self.logger.info(f"已选择年份: {text.strip()}")
                                break
                        else:
                            # 如果没找到年份格式的选项，选择最后一个
                            visible_options.last.click()
                            self.logger.info("已选择最后一个选项")
                            
            except Exception as e:
                # 最后的备用方案：使用键盘导航
                try:
                    year_input = self.browser_service.page.locator('#react-select-5-input')
                    year_input.focus()
                    time.sleep(0.2)
                    self.browser_service.page.keyboard.press('Space')
                    time.sleep(0.3)
                    self.browser_service.page.keyboard.press('End')
                    time.sleep(0.2)
                    self.browser_service.page.keyboard.press('Enter')
                    self.logger.info("通过键盘导航选择了年份")
                except:
                    self.logger.warning(f"选择年份失败: {e}")

            # 等待按钮变为可点击状态（disabled属性消失）
            self.logger.info("等待申请按钮可用...")
            apply_button = self.browser_service.page.wait_for_selector(
                'button:has-text("Apply for academic account"):not([disabled])',
                timeout=15000  # 等待15秒
            )

            # 点击按钮
            self.logger.info("点击申请按钮...")
            apply_button.click()
                
        except Exception as e:
            self.logger.error(f"学习发生错误: {str(e)}")
            # 记录页面状态以便调试
            try:
                page_content = self.browser_service.page.content()
                self.logger.debug(f"当前页面内容片段: {page_content[:500]}...")
            except:
                pass
            return None


    def extract_api_key(self):
        """提取API密钥"""
        # 检查页面是否可用
        if not hasattr(self.browser_service, 'page') or not self.browser_service.page:
            self.logger.error("浏览器页面未初始化，无法提取API密钥")
            return None
            
        try:
            # 直接跳转到API密钥页面
            time.sleep(10)
            self.browser_service.page.goto("https://wandb.ai/authorize", timeout=30 * 1000)
            self.logger.info("已跳转到API密钥页面")
            
            # 等待页面内容加载，使用data-test属性精确定位
            self.logger.info("等待API密钥元素加载...")
            api_key_container = self.browser_service.page.wait_for_selector('[data-test="copyable-API-key"]', timeout=30 * 1000)
            
            if not api_key_container:
                self.logger.error("未找到data-test='copyable-API-key'的元素")
                return None
            
            # 在找到的容器中查找copyable-text-content元素
            content_element = api_key_container.query_selector('.copyable-text-content')
            
            if content_element:
                element_text = content_element.text_content()
                self.logger.info(f"找到API密钥元素，内容: {element_text}")
                
                # 提取API密钥（40位以上的字母数字字符）
                api_key_match = re.search(r'[a-zA-Z0-9_-]{40,}', element_text)
                if api_key_match:
                    api_key = api_key_match.group(0)
                    self.logger.info(f"成功提取API密钥: {api_key[:10]}...")
                    return api_key
                else:
                    self.logger.warning("文本中未找到有效的API密钥格式")
                    return None
            else:
                self.logger.error("未找到copyable-text-content元素")
                return None
                
        except Exception as e:
            self.logger.error(f"提取API密钥时发生错误: {str(e)}")
            # 记录页面状态以便调试
            try:
                page_content = self.browser_service.page.content()
                self.logger.debug(f"当前页面内容片段: {page_content[:500]}...")
            except:
                pass
            return None
    
    def save_account_info(self, email, password, api_key=None, auth_filename='auth.txt', key_filename='key.txt'):
        """保存账户信息到文件"""
        try:
            # 保存账户信息到auth.txt
            with open(auth_filename, 'a', encoding='utf-8') as f:
                if api_key:
                    f.write(f"{email} - {password}  - {api_key}\n")
                else:
                    f.write(f"{email}:{password}\n")
            self.logger.info(f"账户信息已保存到 {auth_filename}")
            
            # 如果有API密钥，也保存到key.txt
            if api_key:
                with open(key_filename, 'a', encoding='utf-8') as f:
                    f.write(f"{api_key}\n")
                self.logger.info(f"API密钥已保存到 {key_filename}")
        except Exception as e:
            self.logger.error(f"保存账户信息时发生错误: {str(e)}")