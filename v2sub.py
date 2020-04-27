#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import os
import requests
import base64
import json
import subprocess
import re
import signal
try: 
    import socks 
except ImportError:
    print("未安装模块Pysocks!现在开始安装...")
    subprocess.call('pip3 install pysocks', shell = True)
    print("请重新运行程序")
    exit()

# 鉴权
if os.geteuid() != 0:
    print("您需要切换到 Root 身份才可以使用本脚本。尝试在命令前加上 sudo?\n")
    exit()

class v2sub():
    def __init__(self):
        self.currentVersion = 1.0
        # 本脚本的配置文件，目前的作用是仅存储用户输入的订阅地址，这样用户再次启动脚本时，就无需再输入订阅地址。
        # 预设的存储的路径为存储到用户的 HOME 内。
        self.subFilePath = os.path.expandvars('$HOME') + '/.v2sub.conf'
        self.subBackupPath = os.path.expandvars('$HOME') + '/.v2sub.conf.backup'
        self.subLinks = []
        self.proxy = 'socks5://127.0.0.1:10808'
        self.currentNode = ''
        self.version = self.currentVersion
        self.serverListLink = []
        self.setServerNodeId = 0
        self.localsub = {}

    def write_v2sub_conf(self):
        # v2sub 配置文件, 不要轻易修改！
        v2subConf = {
            "version": self.currentVersion,
            "subLinks": self.subLinks,
            "proxy": self.proxy,
            "currentNode": self.currentNode,
            "localsub": self.localsub
        }
        json.dump(v2subConf, open(self.subFilePath, 'w'), indent=2)
    #end of write_v2sub_conf


    def write_v2ray_conf(self):
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
                    "vnext": [{
                        "address": self.serverListLink[self.setServerNodeId]['add'],
                        "port": int(self.serverListLink[self.setServerNodeId]['port']),
                        "users": [{
                            "id": self.serverListLink[self.setServerNodeId]['id'],
                            "alterId": int(self.serverListLink[self.setServerNodeId]['aid']),
                            "security": "auto"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": self.serverListLink[self.setServerNodeId]['net'],
                    "security": self.serverListLink[self.setServerNodeId]['tls'],
                    "tlsSettings": {
                        "allowInsecure": False,
                        "serverName": self.serverListLink[self.setServerNodeId]['host']
                    },
                    "wsSettings": {
                        "connectionReuse": True,
                        "path": self.serverListLink[self.setServerNodeId]['path'],
                        "headers": {
                            "Host": self.serverListLink[self.setServerNodeId]['host']
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
    #end of write_v2ray_conf

    #获取节点信息
    def get_nodes(self):
        while True:    
            num = input('选择订阅链接（ctrl+c退出）: ')
            if num.isdigit():
                num = int(num)
                if num not in range(len(self.subLinks)):
                    print("输入的编号不存在！\n")
                    continue
                break
            else:
                print("只能输入数字！")
                continue
        subLink = self.subLinks[num]
        if subLink in self.localsub and not re.search('[noNO]', input("检测到本地已有订阅信息，使用本地信息？[y/n],默认y: ")):
            subb64 = self.localsub[subLink]
            self.serverListLink = base64.b64decode(subb64).splitlines()
        else:
            if self.update_nodes(subLink):
                print("订阅更新成功!")
            else:
                print("订阅更新失败!")
                return False
        for i in range(len(self.serverListLink)):
            serverNode = json.loads(bytes.decode(base64.b64decode(bytes.decode(self.serverListLink[i]).replace('vmess://',''))))
            print('【' + str(i) + '】' + serverNode['ps'])
            self.serverListLink[i] = serverNode
        return True
    #end of get_nodes

    #更新订阅信息
    def update_nodes(self, subLink):
        proxy_flag=False
        proxy_old = "socks5://127.0.0.1:10808"
        if re.search('[yesYES]', input('通过代理获取订阅信息？[y/n] ,默认n：')):
            proxy_flag=True    
            if self.proxy:
                proxy_old = self.proxy
            proxy_new = input('默认代理地址为'+proxy_old+'。请输入地址：')
            if proxy_new and proxy_new !=  proxy_old:
                proxy = proxy_new
            else:
                proxy = proxy_old
            proxies = {'http': proxy, 'https': proxy}
        print("\n开始从订阅地址中读取服务器节点… 如等待时间过久，请检查网络或使用代理。\n")
        # 获取订阅信息
        try:
            if proxy_flag:
                subb64 = requests.get(subLink,proxies=proxies).text + "==="
                self.proxy = proxy
            else:
                subb64 = requests.get(subLink).text + "==="
            self.serverListLink = base64.b64decode(subb64).splitlines()
            self.localsub[subLink] = subb64
        except Exception as e:
            print("订阅地址或代理地址无法连接! 请重新选择或填写.\n异常信息："+str(e))
            return False
        self.write_v2sub_conf()
        return True
    #end of update_nodes

    #切换节点
    def change_node(self):
        while True:    
            self.setServerNodeId = input("\n请输入要切换的节点编号（ctrl+c退出）：")
            if self.setServerNodeId.isdigit():
                self.setServerNodeId = int(self.setServerNodeId)
                if self.setServerNodeId not in range(len(self.serverListLink)):
                    print("输入的编号不存在！\n")
                    continue
                break
            else:
                print("只能输入数字！")
                continue
        subprocess.call('ping ' + self.serverListLink[self.setServerNodeId]['add'] + ' -c 3 -w 10', shell = True)
        if re.search('[yesYES]', input('确定要使用该节点吗？[y/n] ')):
            self.currentNode = self.serverListLink[self.setServerNodeId]['ps']
            self.write_v2ray_conf()
            self.write_v2sub_conf()
            print("\n重启 v2ray 服务……\n")
            subprocess.call('systemctl restart v2ray.service', shell = True)
            print('地址切换完成')
    #end of change_node

    def load_config_file(self):
        # 加载配置文件
        if not os.path.exists(self.subFilePath):
            os.mknod(self.subFilePath)
        
        subFile = open(self.subFilePath, 'r')
        config_json = subFile.read()
        subFile.close()
        
        try:
            config = json.loads(config_json)
            self.subLinks = config['subLinks']
            self.proxy = config['proxy']
            self.currentNode = config['currentNode']
            self.version = config["version"]
            self.localsub = config["localsub"]
        except Exception as e:
            print('\n配置文件解析异常或无配置文件，将重新创建...\n异常信息："+str(e)')
            if os.path.exists(self.subFilePath):
                print('旧配置文件保存在' + self.subBackupPath)
                os.rename(self.subFilePath,self.subBackupPath)
                os.mknod(self.subFilePath)
                subFile = open(self.subFilePath, 'r')
                config_json = subFile.read()
                subFile.close()
    #end of load_config_file

    def main(self):
        self.load_config_file()
        while True:
            if not self.subLinks:
                print('\n您还没有输入订阅地址，请输入订阅地址。')
                subLink = input('订阅地址：')
                self.subLinks.append(subLink)
            print("\n当前节点：" + self.currentNode)
            for i in range(len(self.subLinks)):
                self.subLinks[i]= self.subLinks[i].strip()
                print('订阅链接'+'【' + str(i) + '】：'+self.subLinks[i])
            choose = input('\n1.更换节点 2.增加订阅链接 3.删除订阅链接 , 请输入（输入q退出）：')
            if choose == 'q':
                exit()
            
            #1.更换节点
            if choose == '1':
                if self.get_nodes():
                    self.change_node()
            #2.增加订阅链接
            if choose == '2': 
                subLink = input('订阅地址：')            
                self.subLinks.append(subLink)
                self.write_v2sub_conf()
                continue
            #3.删除订阅链接
            if choose == '3':
                while True:
                    todeleID = input("请输入要删除的订阅编号（ctrl+c退出）：")
                    if todeleID.isdigit():
                        todeleID = int(todeleID)
                    else:
                        print("只能输入数字！")
                        continue
                    if todeleID not in range(len(self.subLinks)):
                        print("输入的编号不存在！\n")
                        continue
                    if re.search('[yesYES]', input('确定要删除该订阅吗？[y/n] : ')):
                        break
                del(self.localsub[self.subLinks[todeleID]])
                del(self.subLinks[todeleID])
                self.write_v2sub_conf()
    #end of main

def v2sub_exit(signum, frame):
  print('\nProgram quit.')
  sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, v2sub_exit)
    signal.signal(signal.SIGTERM, v2sub_exit)    
    sub=v2sub()
    sys.exit(sub.main())
