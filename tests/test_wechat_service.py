import pytest
from unittest.mock import patch
from app.services.wechat_service import WeChatService

@pytest.fixture
def app():
    """创建测试应用"""
    from app import create_app
    app = create_app('testing')
    app.config['WECHAT_APP_ID'] = 'test_app_id'
    app.config['WECHAT_APP_SECRET'] = 'test_app_secret'
    
    with app.app_context():
        yield app

def test_get_access_token(app):
    """测试获取微信access_token"""
    mock_response = {
        'access_token': 'test_access_token',
        'expires_in': 7200,
        'refresh_token': 'test_refresh_token',
        'openid': 'test_openid',
        'scope': 'snsapi_userinfo'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.get_access_token('test_code')
        
        mock_get.assert_called_once_with(
            'https://api.weixin.qq.com/sns/oauth2/access_token',
            params={
                'appid': 'test_app_id',
                'secret': 'test_app_secret',
                'code': 'test_code',
                'grant_type': 'authorization_code'
            }
        )
        
        assert result == mock_response

def test_get_user_info(app):
    """测试获取微信用户信息"""
    mock_response = {
        'openid': 'test_openid',
        'nickname': 'Test User',
        'sex': 1,
        'province': 'Test Province',
        'city': 'Test City',
        'country': 'Test Country',
        'headimgurl': 'http://test.com/avatar.jpg',
        'privilege': [],
        'unionid': 'test_unionid'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.get_user_info('test_access_token', 'test_openid')
        
        mock_get.assert_called_once_with(
            'https://api.weixin.qq.com/sns/userinfo',
            params={
                'access_token': 'test_access_token',
                'openid': 'test_openid',
                'lang': 'zh_CN'
            }
        )
        
        assert result == mock_response

def test_validate_access_token_valid(app):
    """测试验证有效的access_token"""
    mock_response = {
        'errcode': 0,
        'errmsg': 'ok'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.validate_access_token('test_access_token', 'test_openid')
        
        mock_get.assert_called_once_with(
            'https://api.weixin.qq.com/sns/auth',
            params={
                'access_token': 'test_access_token',
                'openid': 'test_openid'
            }
        )
        
        assert result is True

def test_validate_access_token_invalid(app):
    """测试验证无效的access_token"""
    mock_response = {
        'errcode': 40001,
        'errmsg': 'invalid credential'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.validate_access_token('test_access_token', 'test_openid')
        
        mock_get.assert_called_once_with(
            'https://api.weixin.qq.com/sns/auth',
            params={
                'access_token': 'test_access_token',
                'openid': 'test_openid'
            }
        )
        
        assert result is False

def test_get_access_token_error(app):
    """测试获取access_token失败的情况"""
    mock_response = {
        'errcode': 40029,
        'errmsg': 'invalid code'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.get_access_token('invalid_code')
        
        assert result.get('errcode') == 40029

def test_get_user_info_error(app):
    """测试获取用户信息失败的情况"""
    mock_response = {
        'errcode': 40001,
        'errmsg': 'invalid access_token'
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        result = WeChatService.get_user_info('invalid_token', 'test_openid')
        
        assert result.get('errcode') == 40001 