def get_weather(city):
    fake = {
        "深圳":"28度,多云",
        "北京":"15度,晴",
        "上海":"22度,小雨",
    }
    return fake.get(city,f"查不到{city}的天气")
def calculate(expression):
    allowed = set("0123456789+-*/.() ")
    if not set(expression) <= allowed:
        return "表达式不支持该字符"
    try:
        return eval(expression)
    except Exception as e:
        return f"算不出来{e}"
def get_time():
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_time": get_time,
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的当前天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，比如 深圳"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算一个数学表达式，比如 28-15",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "要计算的表达式"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function":{
            "name": "get_time",
            "description":"获取当前时间",
            "parameters": {
                "type": "object",
                "properties": { },

            }
        }
    }
]
