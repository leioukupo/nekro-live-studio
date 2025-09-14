"""
OPENAI API 客户端异常类
"""


class OPENAIAPIException(Exception):
    """openai API 客户端基础异常类"""


class OpenAiAPIError(OPENAIAPIException):
    """API 错误"""

    def __init__(self, error_message, status_code=None):
        self.error_message = error_message
        self.status_code = status_code
        super().__init__(f"API 错误: {error_message} (状态码: {status_code})") 