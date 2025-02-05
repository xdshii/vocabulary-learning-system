import requests
from flask import current_app

class WeChatService:
    @staticmethod
    def get_access_token(code):
        """获取微信access_token"""
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        params = {
            'appid': current_app.config['WECHAT_APP_ID'],
            'secret': current_app.config['WECHAT_APP_SECRET'],
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def get_user_info(access_token, openid):
        """获取微信用户信息"""
        url = 'https://api.weixin.qq.com/sns/userinfo'
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN'
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def validate_access_token(access_token, openid):
        """验证access_token是否有效"""
        url = 'https://api.weixin.qq.com/sns/auth'
        params = {
            'access_token': access_token,
            'openid': openid
        }
        
        response = requests.get(url, params=params)
        return response.json().get('errcode') == 0 