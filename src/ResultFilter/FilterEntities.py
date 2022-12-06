from enum import Enum


class ClassificationType(Enum):
    FALSE_POSITIVE_NOTE = -1  # hermes note信息无法关闭触发的BUG
    FALSE_POSITIVE = 0  # 过滤后被判定为重复的测试结果
    SUSPICIOUS_ENGINE_ERROR = 1  # 可疑的引擎有报错信息
    SUSPICIOUS_ENGINE_NO_ERROR = 2  # 可疑的引擎没有报错信息
    SUSPICIOUS_ALL_NO_EXCEPTION_INFO = 3  # 所有引擎均未报错，只是输出不一致


class FilterType(Enum):
    TYPE1 = 1
    TYPE2 = 2
    TYPE3 = 3
