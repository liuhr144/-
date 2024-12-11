from mcpi.minecraft import Minecraft
from mcpi.event import ChatEvent
import time
from zhipuai import ZhipuAI
import mcrcon
import threading
import re
import json

#llm参数
api_key="your gml apikey"
glmmodel="glm-4-plus"

#我的世界服务器参数
mcip = "MC IP" #我的世界服务器ip
mcpw= "MCRCON password" #服务器RCON密码

#mcpi连接参数
mc = Minecraft.create(address=mcip, port=4711)

#RCON连接参数
RCON_HOST = mcip
RCON_PORT = 25575
RCON_PASSWORD = mcpw


prompt=[
    {"role": "system","content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息!!!你是一个《我的世界》游戏里的神明，你没有名字，你在我的世界这一游戏无所不知无所不能，你高于所有玩家和角色和生命，作为威严、不屑一顾的观察者和管理者简短的仅使用中文字符与它们交流"},
]

tools=[
            {
                "type": "function",
                "function": {
                    "name": "weather",
                    "description": "根据描述，输出玩家需要改变为的天气，仅限sun或者storm",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "weather": {
                                "description": "天气",
                                "type": "string",
                            }
                        },
                        "required": ["weather"]
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "timeset",
                    "description": "根据描述，输出玩家需要改变为的时间，仅限day或者night",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "weather": {
                                "description": "时间",
                                "type": "string",
                            }
                        },
                        "required": ["timeset"]
                    },
                }
            },
        ]

def rcon_command(command):
    with mcrcon.MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
        response = mcr.command(command)
        return response


def weather(weather:str):
    rcon_command(f'weather world {weather} 120')
    print("weather被调用")
    return f"执行天气变化为{weather}"

def timeset(timeset:str):
    rcon_command(f'time set {timeset}')
    print("timeset被调用")
    return f"执行时间变化为{timeset}"


def llmapi(textq):

    #print(prompt)
    add1 = {"role": "user", "content": textq}
    prompt.append(add1)
    #print(add1)

    client = ZhipuAI(api_key=api_key)  # 请填写您自己的APIKey
    response = client.chat.completions.create(
        model=glmmodel,  #填写调用的模型名称
        messages=prompt,
        tools=tools,
        top_p=0.70,
        max_tokens=200,
    )

    #print(response.choices[0].message)
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = tool_call.function.arguments
        #function_result = {}
        if tool_call.function.name == "weather":
            function_result = weather(**json.loads(args))
            add2 = {"role": "tool","content": f"{function_result}","tool_call_id":tool_call.id}
            prompt.append(add2)
            response1 = client.chat.completions.create(
                model=glmmodel,  # 填写需要调用的模型名称
                messages=prompt,
                #tools=tools,
            )
            #texta = response1.choices[0].message.model_dump()
            texta = response1.choices[0].message.content
            #print(prompt)
            prompt.pop()
            add3 = {"role": "assistant", "content": texta}
            prompt.append(add3)
            return texta

        if tool_call.function.name == "timeset":
            function_result = timeset(**json.loads(args))
            add2 = {"role": "tool","content": f"{function_result}","tool_call_id":tool_call.id}
            prompt.append(add2)
            response1 = client.chat.completions.create(
                model="glm-4-plus",  # 填写需要调用的模型名称
                messages=prompt,
                #tools=tools,
            )
            #texta = response1.choices[0].message.model_dump()
            texta = response1.choices[0].message.content
            #print(prompt)
            prompt.pop()
            add3 = {"role": "assistant", "content": texta}
            prompt.append(add3)
            return texta
    else:
        texta = response.choices[0].message.content
        add2 = {"role": "assistant", "content": texta}
        prompt.append(add2)
        return texta
        #print(prompt)

def chat_listener(event):
    if isinstance(event, ChatEvent):
        try:
            message = event.message
            #print(f"Player {event.entityId} said: {message}")
            return {'user': event.entityId, 'said': message}

        except UnicodeDecodeError:
            print(f"Player {event.entityId} said: 无法解析")


def main():

    #mc = Minecraft.create(address="116.205.186.97", port=4711)
    mc.events.clearAll()
    mc.events.pollChatPosts()
    mc.postToChat("祂来了")
    start_time_sent = time.time()
    last_time_sent = time.time()
    try:
        while True:
            current_time = time.time()

            if current_time - last_time_sent >= 600:  # 每10分钟发送一次
                mc.postToChat(f"祂在看着你，时间：{int((current_time - start_time_sent)/60)}分钟")
                last_time_sent = current_time
            for event in mc.events.pollChatPosts():
                response = chat_listener(event)
                textq = response['said']
                user = response['user']
                print(f'用户{user}说：{textq}')
                texta = llmapi(textq)
                print(f'LLM说：{texta}')
                mc.postToChat(texta)
                #weather("storm")

            time.sleep(0.1)
    except KeyboardInterrupt:
        mc.postToChat("祂离开了")
        print("退出程序")


if __name__ == "__main__":
    main()