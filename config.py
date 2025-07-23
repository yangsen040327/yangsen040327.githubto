# Flask应用配置
class Config:
    # 开启调试模式
    DEBUG = True
    
    # 模板自动重载
    TEMPLATES_AUTO_RELOAD = True
    
    # 静态文件缓存控制
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # 允许的静态文件扩展名
    STATIC_EXTENSIONS = ['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'svg']
    
    # API配置
    API_PREFIX = '/api'
    API_VERSION = 'v1'
