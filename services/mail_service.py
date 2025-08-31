import requests
import time
import logging
import re
from config.settings import DEFAULT_TIMEOUT, PROXY_URL, parse_proxy_url

class MailApiClient:
    """临时邮件API客户端 - 使用94.16.122.36:8000 API"""
    
    def __init__(self):
        self.base_url = "http://94.16.122.36:8000"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # 配置代理
        if PROXY_URL:
            proxy_config = parse_proxy_url(PROXY_URL)
            if proxy_config:
                proxies = {
                    'http': PROXY_URL,
                    'https': PROXY_URL
                }
                self.session.proxies.update(proxies)
                self.logger.info(f"已配置代理: {PROXY_URL}")
    
    def create_email_address(self):
        """创建新的临时邮件地址"""
        try:
            response = self.session.get(
                f"{self.base_url}/new",
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                email_data = response.json()
                email = email_data.get('email')
                if email:
                    self.logger.info(f"成功创建临时邮箱: {email}")
                    return email
                else:
                    self.logger.error("API返回的响应中没有email字段")
                    return None
            else:
                self.logger.error(f"创建邮箱失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"创建邮箱时发生错误: {str(e)}")
            return None
    
    def get_messages(self, email):
        """获取指定邮箱的邮件列表"""
        try:
            response = self.session.get(
                f"{self.base_url}/rec/{email}",
                timeout=DEFAULT_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('emails', [])
                count = data.get('count', 0)
                self.logger.info(f"获取到 {count} 封邮件")
                return emails
            else:
                self.logger.error(f"获取邮件列表失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取邮件列表时发生错误: {str(e)}")
            return []
    
    def poll_messages(self, email, max_wait_time=30):
        """轮询获取邮件，直到收到邮件或超时"""
        start_time = time.time()
        check_interval = 5  # 每5秒检查一次
        
        self.logger.info(f"开始轮询邮件，最多等待 {max_wait_time} 秒...")
        
        while time.time() - start_time < max_wait_time:
            messages = self.get_messages(email)
            if messages:
                return messages
            
            remaining_time = max_wait_time - int(time.time() - start_time)
            self.logger.info(f"暂未收到邮件，{check_interval}秒后重试...（剩余等待时间: {remaining_time} 秒）")
            time.sleep(check_interval)
        
        self.logger.warning(f"⚠️ {max_wait_time}秒内未收到邮件")
        return []
    
    def get_verification_link(self, email, max_wait_time=60):
        """获取Wandb验证链接"""
        try:
            # 轮询邮件
            self.logger.info(f"开始获取验证邮件，邮箱: {email}")
            messages = self.poll_messages(email, max_wait_time)
            
            if not messages:
                self.logger.warning("⚠️ 轮询结束，未收到任何邮件")
                return None
            
            self.logger.info(f"收到 {len(messages)} 封邮件，开始分析...")
            
            # 首先打印所有邮件的结构，用于调试
            for i, message in enumerate(messages):
                self.logger.info(f"邮件 {i+1} 结构: {type(message)} - {message}")
            
            for message in messages:
                # 查找来自 support@wandb.com 的验证邮件
                # 处理不同的邮件格式
                if isinstance(message, dict):
                    from_address = message.get('from', message.get('from_address', '')).lower()
                    subject = message.get('subject', message.get('title', ''))
                    body = message.get('body', message.get('content', message.get('text', '')))
                else:
                    # 如果不是字典，可能是字符串或其他格式
                    self.logger.warning(f"邮件格式异常: {type(message)} - {message}")
                    continue
                
                self.logger.info(f"检查邮件: 发件人={from_address}, 主题={subject}")
                self.logger.debug(f"邮件内容长度: {len(body)} 字符")
                
                # 更宽松的匹配条件
                if ('wandb' in from_address.lower() or 
                    'wandb' in subject.lower() or 
                    'verify' in subject.lower() or
                    'auth0' in body.lower()):
                    
                    self.logger.info(f"找到可能来自 wandb 的邮件: {subject}")
                    self.logger.info(f"邮件内容预览: {body[:200]}...")
                    
                    # 提取验证链接
                    # 匹配包含 wandb.auth0.com 的完整链接
                    links = re.findall(r'https?://wandb\.auth0\.com[^\s<>"\)]+', body)
                    if links:
                        verification_link = links[0]
                        self.logger.info(f"成功找到验证链接: {verification_link}")
                        return verification_link
                    else:
                        self.logger.warning("邮件中未找到验证链接，尝试其他匹配方式...")
                        # 尝试其他可能的链接格式
                        all_links = re.findall(r'https?://[^\s<>"\)]+', body)
                        auth0_links = [link for link in all_links if 'auth0.com' in link]
                        if auth0_links:
                            verification_link = auth0_links[0]
                            self.logger.info(f"找到 auth0 链接: {verification_link}")
                            return verification_link
                else:
                    self.logger.debug(f"跳过非wandb邮件: {from_address} - {subject}")
            
            self.logger.warning("在收到的邮件中未找到wandb验证邮件")
            return None
            
        except Exception as e:
            self.logger.error(f"获取验证链接时发生错误: {str(e)}")
            return None