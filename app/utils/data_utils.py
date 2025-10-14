"""数据处理工具函数"""
from typing import Any


def extract_text_from_any(data: Any) -> str:
    """
    从任意数据格式中提取文本内容

    支持的数据类型：
    - str: 直接返回
    - dict: 拼接为 "key: value; key: value" 格式
    - list/tuple: 拼接为 "item1, item2" 格式
    - 其他: 转换为字符串

    Args:
        data: 任意类型的数据

    Returns:
        提取的文本内容

    Examples:
        >>> extract_text_from_any("Hello World")
        'Hello World'

        >>> extract_text_from_any({"门票": "60元", "时间": "8:00-17:00"})
        '门票: 60元; 时间: 8:00-17:00'

        >>> extract_text_from_any(["地铁1号线", "公交1路"])
        '地铁1号线, 公交1路'
    """
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        # 如果是字典，拼接所有键值对
        parts = []
        for key, value in data.items():
            if isinstance(value, (list, tuple)):
                parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                nested = extract_text_from_any(value)
                parts.append(f"{key}: {nested}")
            else:
                parts.append(f"{key}: {value}")
        return "; ".join(parts)
    elif isinstance(data, (list, tuple)):
        # 如果是列表或元组，拼接所有元素
        return ", ".join(str(item) for item in data)
    else:
        # 其他类型转换为字符串
        return str(data)
