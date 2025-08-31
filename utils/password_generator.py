import random
import string

def generate_secure_password(length=12):
    """生成安全密码（至少10位，包含大小写字母和特殊字符）"""
    if length < 10:
        length = 10
    
    # 确保密码包含各种字符类型
    lowercase = random.choice(string.ascii_lowercase)
    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%^&*()_+-=[]{}|;:,.<>?')
    
    # 剩余字符随机生成
    remaining_length = length - 4
    all_characters = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
    remaining_chars = ''.join(random.choice(all_characters) for _ in range(remaining_length))
    
    # 组合所有字符并打乱顺序
    password = lowercase + uppercase + digit + special + remaining_chars
    password_list = list(password)
    random.shuffle(password_list)
    return ''.join(password_list)