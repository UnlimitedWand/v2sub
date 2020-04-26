#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import os
import requests
import base64
import json
import subprocess
import re

# 鉴权
if os.geteuid() != 0:
    print("您需要切换到 Root 身份才可以使用本脚本。尝试在命令前加上 sudo?\n")
    exit()

# 本脚本的配置文件，目前的作用是仅存储用户输入的订阅地址，这样用户再次启动脚本时，就无需再输入订阅地址。
# 预设的存储的路径为存储到用户的 HOME 内。
subFilePath = os.path.expandvars('$HOME') + '/.v2sub.conf'
# 获取订阅地址
if not os.path.exists(subFilePath):
    os.mknod(subFilePath)

subFile = open(subFilePath, 'r')
subLinks = subFile.readlines()
subFile.close()

while True:
    if not subLinks:
        print('\n您还没有输入订阅地址，请输入订阅地址。')
        subLink = input('订阅地址：')
        subFile = open(subFilePath, 'w+')
        subFile.write(subLink)
        subFile.seek(0,0);
        subLinks = subFile.readlines()
        subFile.close()
    print("\n当前订阅：")
    for i in range(len(subLinks)):
        subLinks[i]= subLinks[i].strip()
        print('订阅链接'+'【' + str(i) + '】：'+subLinks[i])
    choose = input('\n1.更换节点 2.增加订阅链接 3.删除订阅链接 , 请输入（输入q退出）：')
    if choose == 'q':
        exit()
    if choose == '1':
        break    
    if choose == '2':
        subLink = input('订阅地址：')            
        subFile = open(subFilePath, 'a+')
        subFile.write('\n'+subLink)
        subFile.seek(0,0);
        subLinks = subFile.readlines()
        subFile.close()

    if choose == '3':
        while True:
            todeleID = input("请输入要删除的订阅编号：")
            if todeleID.isdigit():
                todeleID = int(todeleID)
            else:
                print("只能输入数字！")
                continue
            if todeleID not in range(len(subLinks)):
                print("输入的编号不存在！\n")
                continue
            if re.search('[yesYES]', input('确定要删除该订阅吗？[y/N] ')):
                break
        del(subLinks[todeleID])
        subFile = open(subFilePath, 'w')
        subFile.writelines(line + '\n' for line in subLinks)
        subFile.close()


while True:    
    link = input('选择订阅链接: ')
    if link.isdigit():
        link = int(link)
        if link not in range(len(subLinks)):
            print("输入的编号不存在！\n")
            continue
        break
    else:
        print("只能输入数字！")
        continue
subLink = subLinks[link]
print("\n开始从订阅地址中读取服务器节点… 如等待时间过久，请检查网络。\n")
# 获取订阅信息
serverListLink = base64.b64decode(requests.get(subLink).text + "===").splitlines()
for i in range(len(serverListLink)):
    serverNode = json.loads(bytes.decode(base64.b64decode(bytes.decode(serverListLink[i]).replace('vmess://',''))))
    print('【' + str(i) + '】' + serverNode['ps'])
    serverListLink[i] = serverNode

while True:
    while True:    
        setServerNodeId = input("\n请输入要切换的节点编号：")
        if setServerNodeId.isdigit():
            setServerNodeId = int(setServerNodeId)
            if setServerNodeId not in range(len(serverListLink)):
                print("输入的编号不存在！\n")
                continue
            break
        else:
            print("只能输入数字！")
            continue
    subprocess.call('ping ' + serverListLink[setServerNodeId]['add'] + ' -c 3 -w 10', shell = True)
    if re.search('[yesYES]', input('确定要使用该节点吗？[y/N] ')):
        break

# 编辑 v2ray 配置文件
v2rayConf = {
  "inbound": {
    "port": 10808,
    "listen": "127.0.0.1",
    "protocol": "socks",
	"sniffing": {
        "enabled": True,
        "destOverride": [
          "http",
          "tls"
        ]
    },
	"settings": {
		"auth": "noauth",
        "udp": True,
		"ip": "127.0.0.1"
    }
  },
  "outbound": {
    "tag": "proxy",
    "protocol": "vmess",
    "settings":{ 
        "vnext": [
          {
            "address": serverListLink[setServerNodeId]['add'],
            "port": int(serverListLink[setServerNodeId]['port']),
            "users": [
              {
                "id": serverListLink[setServerNodeId]['id'],
                "alterId": int(serverListLink[setServerNodeId]['aid']),
				"security": "auto"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": serverListLink[setServerNodeId]['net'],
        "security": serverListLink[setServerNodeId]['tls'],
        "tlsSettings": {
          "allowInsecure": False,
          "serverName": serverListLink[setServerNodeId]['host']
        },
        "wsSettings": {
          "connectionReuse": True,
          "path": serverListLink[setServerNodeId]['path'],
          "headers": {
            "Host": serverListLink[setServerNodeId]['host']
          }
        }
      },
      "mux": {
        "enabled": False,
        "concurrency": -1
      }
    },
  "outboundDetour": [{
    "protocol": "freedom",
    "tag": "direct",
    "settings": {}
  }],
  "routing": {
    "strategy": "rules",
    "settings": {
      "domainStrategy": "IPOnDemand",
      "rules": [{
        "type": "field",
        "ip": [
          "0.0.0.0/8",
          "10.0.0.0/8",
          "100.64.0.0/10",
          "127.0.0.0/8",
          "169.254.0.0/16",
          "172.16.0.0/12",
          "192.0.0.0/24",
          "192.0.2.0/24",
          "192.168.0.0/16",
          "198.18.0.0/15",
          "198.51.100.0/24",
          "203.0.113.0/24",
          "::1/128",
          "fc00::/7",
          "fe80::/10"
        ],
        "outboundTag": "direct"
      }]
    }
  }
}

json.dump(v2rayConf, open('/etc/v2ray/config.json', 'w'), indent=2)

print("\n重启 v2ray 服务……\n")
subprocess.call('systemctl restart v2ray.service', shell = True)

print('地址切换完成')

exit()
