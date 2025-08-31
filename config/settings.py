import os
import urllib.parse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 注册后配置
FULL_NAME = os.getenv('FULL_NAME', 'Zhi Yang')
COMPANY_NAME = os.getenv('COMPANY_NAME', 'Linux Do')

# 默认配置
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_ATTEMPTS = 3

# 注册执行次数配置
REGISTRATION_COUNT = int(os.getenv('REGISTRATION_COUNT', 1))

# Headless模式配置
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'false').lower() in ('true', '1', 'yes')

# 代理配置
PROXY_URL = os.getenv('PROXY_URL', None)


def parse_proxy_url(proxy_url):
    """解析代理URL并返回代理配置字典"""
    if not proxy_url:
        return None
    
    parsed = urllib.parse.urlparse(proxy_url)
    
    proxy_config = {
        'scheme': parsed.scheme,
        'hostname': parsed.hostname,
        'port': parsed.port,
        'username': parsed.username,
        'password': parsed.password
    }
    
    return proxy_config