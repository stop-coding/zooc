# -*- encoding: utf-8 -*-
'''
@File    :   zooc.py
@Time    :   2021/04/15 15:48:29
@Author  :   hongchunhua
@Contact :   hongchunhua@ruijie.com.cn;549599715@qq.com
@License :   (C)Copyright 2020-2025
'''
import re
from kazoo.client import KazooClient
from kazoo.protocol.states import (
    KeeperState,
)
from kazoo.exceptions import *
import time
import sys, getopt
import tty
import termios
import os

class zkLogger(object):
    def error(self, log):
        print("ERROR : ", log)
    def info(self, log):
        print("INFO : ", log)
    def WARN(self, log):
        print("WARN : ", log)
    def show(self, log):
        print(log)
    def show_r(self, log):
        print(log, end='', flush=True)

# 抽象类
class cmdFunc(object):
    def __init__(self):
        self.log = zkLogger()
    def print_head(self):
        self.log.show("---")
    def tab(self, t, cmd):
        try:
            path = ''
            cmds = cmd.split(' ')
            opts, args = getopt.getopt(cmds[1:], "p:", ['path='])
            for opt, val in opts:
                if opt in ('-p', '--path'):
                    path = val
                    if len(path) == 0:
                        path='/'
            cmd = t.auto_complete_zkpath(path, cmd)
        except Exception as e:
            self.log.error("addwatch tab: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def print_body(self):
        pass
    def print_front(self):
        self.log.show("")
    def msg(self):
        self.print_head()
        self.print_body()
        self.print_front()

    def parse(self, cmd):
        pass
    def run(self, Kazooc):
        pass

class addwatch(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path='/'
        self.type='get'
        self.is_forever=False
        self.is_err=False
        self.method={'get':self.addWatchForGet, 'exist':self.addWatchForGetChild, 'child':self.addWatchForExist}
    def print_body(self):
        self.log.show("usage: addwatch [--forever] -t [get/exist/child] -p [path]")
        self.log.show("  --forever    一直监听，默认是一次触发")
        self.log.show("  -t,--type    watch类型:")
        self.log.show("               get 能监控自身节点的删除,以及自身节点数据的修改")
        self.log.show("               exist 能监控自身节点的删除,以及自身节点数据的修改")
        self.log.show("               child 能监控自身节点的删除,不能监控自身节点数据的修改,能监控子节点的增加和删除,不能监控子节点数据的修改不能监控孙子节点的增加")
        self.log.show("  -p,--path    watch path")
    def parse(self, opt):
        try:
            self.is_forever=False
            opts, args = getopt.getopt(opt, "ht:p:", ["help", "type=", 'path=','forever'])
            for cmd, val in opts:
                if cmd in ('-h', '--help'):
                    self.msg()
                    continue
                if cmd in ('-t', '--type'):
                    if val in ('get', 'exist', 'child'):
                        self.type=val
                    else:
                        self.log.error("unkown type=" + val)
                        self.msg()
                    continue
                if cmd in ('-p', '--path'):
                    self.path=val
                    continue
                if cmd in ('--forever'):
                    self.is_forever = True
                    continue
                self.is_err = True
                return
        except Exception as e:
            self.log.error("getopt: {0}".format(e))

    def addWatchForGet(self, Kazooc):
        try:
            node = ''
            if self.is_forever:
                node = Kazooc.client.get(self.path, watch=Kazooc.recursive_watch_cb_get)
            else:
                node = Kazooc.client.get(self.path, watch=Kazooc.watch_cb_get)
            self.log.show(node)
        except Exception as e:
            self.log.error("zk watch get: {0}".format(e))

    def addWatchForGetChild(self, Kazooc):
        try:
            node = ''
            if self.is_forever:
                node = Kazooc.client.get_children(self.path, watch=Kazooc.recursive_watch_cb_get_child)
            else:
                node = Kazooc.client.get_children(self.path, watch=Kazooc.watch_cb_get_child)
            self.log.show(node)
        except Exception as e:
            self.log.error("zk watch get child: {0}".format(e))
    def addWatchForExist(self, Kazooc):
        try:
            node = ''
            if self.is_forever:
                node = Kazooc.client.exists(self.path, watch=Kazooc.recursive_watch_cb_exists)
            else:
                node = Kazooc.client.exists(self.path, watch=Kazooc.watch_cb_exists)
            self.log.show(node)
        except Exception as e:
            self.log.error("zk watch exists: {0}".format(e))

    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        if self.type in self.method:
            self.method[self.type](Kazooc)

class zk_create(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path='/'
        self.data=b''
        self.is_err=False
        self.is_ephemeral=False
    def print_body(self):
        self.log.show("usage: create [-e] -p [path] -d [data]")
        self.log.show("  -e    临时节点")
        self.log.show("  -p,--path    新建路径")
        self.log.show("  -d,--data    设置值，可选")
    def parse(self, opt):
        try:
            opts, args = getopt.getopt(opt, "hep:d:", ["help", 'path=','data='])
            for cmd, val in opts:
                if cmd in ('-h', '--help'):
                    self.msg()
                    continue
                if cmd in ('-e'):
                    self.is_ephemeral = True
                    continue
                if cmd in ('-p', '--path'):
                    self.path=val
                    continue
                if cmd in ('-d', '--data'):
                    self.data=val
                    continue
                self.is_err = True
                return
        except Exception as e:
            self.log.error("getopt: {0}".format(e))
    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        try:
            if len(self.data):
                Kazooc.client.create(self.path, bytes(self.data, encoding='utf-8'), ephemeral=self.is_ephemeral)
            else:
                Kazooc.client.create(self.path, ephemeral=self.is_ephemeral)
        except Exception as e:
            self.log.error("zk create: {0}".format(e))

class zk_delete(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path=''
        self.is_err=False
    def print_body(self):
        self.log.show("usage: delete  [path]")
    def tab(self, t, cmd):
        try:
            cmds = cmd.split(' ')
            if len(cmds) > 1:
                cmd = t.auto_complete_zkpath(cmds[1], cmd)
        except Exception as e:
            self.log.error("ls tab: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        try:
            if len(opt) == 1:
                parent,node = os.path.split(opt[0])
                self.path = os.path.join(parent, node)
            else:
                self.path=''
                self.is_err = True
        except Exception as e:
            self.log.error("zk_get: {0}".format(e))
    
    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        try:
            Kazooc.client.delete(self.path)
        except Exception as e:
            self.log.error("zk delete: {0}".format(e))

class zk_set(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path='/zookeeper'
        self.data=''
        self.is_err=False
    def print_body(self):
        self.log.show("set -p [path] -d [data]")
        self.log.show("  -p,--path    新建路径")
        self.log.show("  -d,--data    设置值")
    def parse(self, opt):
        try:
            opts, args = getopt.getopt(opt, "hep:d:", ["help", 'path=','data='])
            for cmd, val in opts:
                if cmd in ('-h', '--help'):
                    self.msg()
                    continue
                if cmd in ('-p', '--path'):
                    self.path=val
                    continue
                if cmd in ('-d', '--data'):
                    self.data=val
                    continue
                self.is_err = True
                return
        except Exception as e:
            self.log.error("getopt: {0}".format(e))
    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        try:
            Kazooc.client.set(self.path, bytes(self.data, encoding='utf-8'))
        except Exception as e:
            self.log.error("zk set: {0}".format(e))

class zk_list(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path='/'
        self.data=''
        self.is_err=False
    def print_body(self):
        self.log.show("usage: ls [path]")
        self.log.show("  path    查询的路径")
    def tab(self, t, cmd):
        try:
            cmds = cmd.split(' ')
            if len(cmds) > 1:
                cmd = t.auto_complete_zkpath(cmds[1], cmd)
        except Exception as e:
            self.log.error("ls tab: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        if len(opt) == 1:
            parent,node = os.path.split(opt[0])
            self.path = os.path.join(parent, node)
        else:
            self.path = '/'
    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        try:
            dirs = Kazooc.client.get_children(self.path)
            self.log.show(dirs)
        except Exception as e:
            self.log.error("zk ls: {0}".format(e))

class zk_get(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.path='/'
        self.is_err=False
    def print_body(self):
        self.log.show("usage: get [path]")
        self.log.show("   path    路径")
    def tab(self, t, cmd):
        try:
            cmds = cmd.split(' ')
            if len(cmds) > 1:
                cmd = t.auto_complete_zkpath(cmds[1], cmd)
            else:
                self.msg()
        except Exception as e:
            self.log.error("ls tab: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        try:
            if len(opt) == 1:
                parent,node = os.path.split(opt[0])
                self.path = os.path.join(parent, node)
            else:
                self.path='/'
                self.msg()
                self.is_err = True
        except Exception as e:
            self.log.error("zk_get: {0}".format(e))
    def run(self, Kazooc):
        if self.is_err:
            self.is_err = False
            return
        try:
            node = Kazooc.client.get(self.path)
            self.log.show(node)
        except Exception as e:
            self.log.error("zk get: {0}".format(e))

class zk_cmd(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.cmd='stat'
        self.cmds = ('stat', 'envi', 'conf', 'dump', 'cons', "wchc", 'mntr')
        self.is_err=False
    def print_body(self):
        self.log.show("usage: nc [type]")
        self.log.show("  type：")
        self.log.show("      stat    查看当节点状态")
        self.log.show("      envi    输出当前服务器所运行的环境信息")
        self.log.show("      conf    查看当节点配置")
        self.log.show("      dump    输出集群所有的会话信息，包活会话信息id，以及每个会话创建的临时节点的信息")
        self.log.show("      cons    当前服务器上所有客户端的链接的详细信息")
        self.log.show("      wchc    当前服务器上watcher的详细信息，以会话为单位进行分组显示")
        self.log.show("      wchp    当前服务器上管理的watcher信息")
        self.log.show("      mntr    输出比stat命令更为详细的服务器统计信息")
    def tab(self, t, cmd):
        try:
            cmds = cmd.split(' ')
            print(cmds, len(cmds))
            if len(cmds) > 1 and len(cmds[1]):
                if cmds[1] in self.cmds:
                    pass
                else:
                    out_cmd=''
                    for name in self.cmds:
                        if re.match(cmds[1], name):
                            out_cmd = name
                            break
                    if len(out_cmd):
                        cmd = cmd.replace(cmds[1], out_cmd)
            else:
                self.msg()
        except Exception as e:
            self.log.error("cmd: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        if len(opt) == 0:
            self.is_err=True
            return
        if opt[0] in self.cmds:
            self.cmd = opt[0]
        else:
            self.cmd=''
            self.is_err=True
    def run(self, Kazooc):
        if self.is_err:
            self.is_err=False
            return
        try:
            rsp = Kazooc.client.command(self.cmd.encode())
            self.log.show(rsp)
        except Exception as e:
            self.log.error("zk nc: {0}".format(e))

class zk_info(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.cmd='info'
        self.is_err=False
        self.message = ('Mode', )
    def print_body(self):
        self.log.show("usage: info")
        self.log.show("      info    查看集群状态状态")
    def tab(self, t, cmd):
        try:
            self.msg()
        except Exception as e:
            self.log.error("cmd: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        self.is_err=False
    def run(self, Kazooc):
        if self.is_err:
            self.is_err=False
            return
        try:
            infos = {}
            for client in Kazooc.servers:
                infos[client] = Kazooc.servers[client].command('stat'.encode()).split('\n')
            for client in infos:
                for stat in infos[client]:
                    key = stat.split(':')
                    if key[0] in self.message:
                         print(client + '-> ' +stat)
        except Exception as e:
            self.log.error("zk info: {0}".format(e))

class zk_set_participant(cmdFunc):
    def __init__(self):
        self.log = zkLogger()
        self.cmd='par'
        self.is_err=False
        self.message = ('Mode', )
    def print_body(self):
        self.log.show("usage: par")
        self.log.show("      par    设置全部为参与者")
    def tab(self, t, cmd):
        try:
            self.msg()
        except Exception as e:
            self.log.error("cmd: {0}".format(e))
            self.msg()
        finally:
            return cmd
    def parse(self, opt):
        self.is_err=False
    def run(self, Kazooc):
        if self.is_err:
            self.is_err=False
            return
        try:
            rsp = Kazooc.client.command("conf".encode())
            for cfg in rsp.split():
                if re.match(r'server\.(.*)=(.*:)?', cfg) is None:
                    continue
                if re.match(r'(.*)observer(.*)', cfg) is None:
                    continue
                print(cfg)
                change = cfg.replace("observer", "participant", 1)
                self.do_reconfig(Kazooc.client, change)
        except Exception as e:
            self.log.error("zk info: {0}".format(e))
    
    def do_reconfig(self, zk, new=[]):
        retry = False
        try:
            max_wait_time = 10
            #重试间隔时间，单位秒
            wait_interval = 0.5
            while not zk.connected:
                time.sleep(wait_interval)
                max_wait_time -= wait_interval
                if max_wait_time <= 0:
                    self.log.error(" session can't reconnected.")
                    raise ZookeeperError
            zk.reconfig(joining=new, leaving=None, new_members=None)
        except NewConfigNoQuorumError as e:
            self.log.error("NewConfigNoQuorumError: {}".format(e))
        except BadVersionError as e:
            self.log.error(" bad version: {}".format(e))
        except BadArgumentsError as e:
            self.log.error(" bad arguments: {}".format(e))
        except ZookeeperError as e:
            retry = True
        except Exception as e:
            self.log.error(" unknown error: {}".format(e))
            raise e
        finally:
            return retry

class zkClient(object):
    def __init__(self, timeout=3.0, showTxt = '[]# ', zkhost='127.0.0.1:2188'):
        self.log = zkLogger()
        self.zk_state = ''
        self.client = None
        self.session_id = ''
        self.timeout = timeout
        self.showtxt = showTxt
        self.host = zkhost
        self.servers = {}
    def __del__(self):
        self.close()
    
    def listener(self, state):
        print(state)
        self.zk_state = state
        self.log.info("zks event, zkstate=%s" %(repr(self.zk_state)))
    def get_severs(self, client):
        servers = [client]
        return servers
    def connect(self, host, timeout = 0.5):
        client = None
        try:
            #self.log.info('client connect server=%s, timeout=%s' %(str(host), str(self.timeout)))
            client = KazooClient(
                hosts=host,
                timeout=timeout
            )
            client.add_listener(self.listener)
            client.start(1)
        except Exception as e:
            self.log.error('client connect server=%s, timeout=%s' %(str(host), str(timeout)))
            self.log.error("Cannot connect to Zookeeper: {0}".format(e))
            self.zk_state = "CLOSED"
            client = None
        finally:
            return client
    def close(self):
        try:
            for client in self.servers:
                self.servers[client].stop()
                self.servers[client].close()
        except Exception as e:
            self.log.error("close: {0}".format(e))

    def open(self):
        try:
            self.close()
            hosts = self.host.split(',')
            for host in hosts:
                self.client = self.connect(host, self.timeout)
                if self.client == None:
                    raise ValueError("client connect fail")
                self.servers[host] = self.client
            servers = self.get_severs(self.client)
            for server in servers:
                if server in self.servers:
                    continue
                client = self.connect(server, 0.5)
                if client == None:
                    continue
                self.servers[server] = client 
        except Exception as e:
            raise e
        if self.client != None:
            (self.session_id,pwd) = self.client.client_id
            self.log.info("zk connected success, session id [0x%x]!!" %(self.session_id))
            return True
        return False

    def watch_cb_get(self, event):
        self.log.show("get notify for path [%s]" %(event.path))
        newnode = self.client.get(event.path)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)

    def watch_cb_exists(self, event):
        self.log.show("get exists notify for path [%s]" %(event.path))
        newnode = self.client.exists(event.path)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)

    def watch_cb_get_child(self, event):
        self.log.show("get child notify for path [%s]" %(event.path))
        newnode = self.client.get_children(event.path)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)
    
    def recursive_watch_cb_get(self, event):
        self.log.show("get notify for path [%s]" %(event.path))
        newnode = self.client.get(event.path, watch=self.recursive_watch_cb_get)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)

    def recursive_watch_cb_exists(self, event):
        self.log.show("get exists notify for path [%s]" %(event.path))
        newnode = self.client.exists(event.path, watch=self.recursive_watch_cb_exists)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)
    def recursive_watch_cb_get_child(self, event):
        self.log.show("get child notify for path [%s]" %(event.path))
        newnode = self.client.get_children(event.path, watch=self.recursive_watch_cb_get_child)
        self.log.show(newnode)
        self.log.show_r(self.showtxt)

    def list_path(self, path):
        nodes = []
        try:
            if self.client.exists(path) is not None:
                nodes = self.client.get_children(path)
            else:
                parent, child = os.path.split(path)
                cList = self.client.get_children(parent)
                if child in cList:
                    nodes.append(child)
                else:
                    for node in cList:
                        if re.match(child, node):
                            nodes.append(node)
                    if len(nodes) == 0:
                        nodes.append(child)
        except Exception as e:
            self.log.error("list_path: {0}".format(e))
        finally:
            return nodes
class cmdInput(object):
    KEY_TAB = 'tab'
    KEY_EXIT = 'exit'
    KEY_ENTER = 'enter'

    def __init__(self, showtxt='[]# '):
        self.log = zkLogger()
        self.break_cmds  ={'0x9':self.KEY_TAB, '0x3':self.KEY_EXIT, '0xd':self.KEY_ENTER,}
        self.indata = ''
        self.showtxt = showtxt
        self.history_cmd=[]
        self.action={'0x8':self.do_delete, '0x1b0x5b0x41':self.do_previous_cmd,'0x1b0x5b0x42':self.do_next_cmd}
    
    def strToHexStr(str):
        ret=''
        for ch in str:
            ret+= '%#x'%ord(ch)
        return ret
    
    def clearShowNew(self, old, new):
        if len(old):
            print(chr(27) + "[%dD" %(len(old)), end='', flush=True)
            print(chr(27) + "[K", end='', flush=True)
        print(new, end='', flush=True)

    def do_end(self, key, data):
        if key == self.KEY_TAB:
            return
        if self.history_cmd.count(data) > 0:
            return
        if len(data) == 0:
            return
        self.history_cmd.append(data)
        if len(self.history_cmd) > 100:
            self.history_cmd.pop(0)

    def do_delete(self):
        if len(self.indata) == 0:
            return
        print(chr(27) + "[1D", end='', flush=True)
        print(chr(27) + "[K", end='', flush=True)
        self.indata = self.indata[:-1]

    def do_previous_cmd(self):
        if len(self.history_cmd) == 0:
            return
        if len(self.indata):
            self.history_cmd.insert(0, self.indata)
        old = self.indata
        self.indata = self.history_cmd.pop()
        self.history_cmd.insert(0, self.indata)
        self.clearShowNew(old, self.indata)

    def do_next_cmd(self):
        if len(self.history_cmd) == 0:
            return
        if len(self.indata):
            self.history_cmd.append(self.indata)
        old = self.indata
        self.indata = self.history_cmd.pop(0)
        self.history_cmd.append(self.indata)
        self.clearShowNew(old, self.indata)


    def strToHexStr(self, str):
        ret=''
        for ch in str:
            ret+= '%#x'%ord(ch)
        return ret
    
    def get(self, cmd='', show=''):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        key = self.KEY_ENTER
        if len(show):
            self.showtxt = show
        self.log.show_r(self.showtxt + cmd)
        self.indata = cmd
        try:
            combination=''
            while True:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                charhex = self.strToHexStr(ch)
                if charhex == "0x1b":
                    combination += ch
                    continue
                if len(combination) > 0:
                    combination+=ch
                    if len(combination) == 3:
                        charhex = self.strToHexStr(combination)
                        combination = ''
                        ch = ''
                    else:
                        continue
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                if charhex in self.break_cmds:
                    key = self.break_cmds[charhex]
                    break
                elif charhex in self.action:
                    self.action[charhex]()
                    continue
                elif len(ch) and ch.isprintable():
                    print(ch, end='', flush=True)
                    self.indata+=ch
                else:
                    pass  
        except Exception as e:
            self.log.error("get: {0}".format(e))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.do_end(key, self.indata)
            print('')
        return key, self.indata

class terminal(object):
    def __init__(self, name='zooc', t = 15.0, host = '127.0.0.1:2188'):
        self.log = zkLogger()
        self.zk = zkClient(timeout = t, zkhost = host)
        self.keyset = {cmdInput.KEY_TAB:self.do_tab, cmdInput.KEY_ENTER:self.do_enter, cmdInput.KEY_EXIT:self.do_exit, }
        self.funcs = {"addwatch":addwatch(), 'create':zk_create(), 'del':zk_delete(), 
                     'set':zk_set(), 'get':zk_get(), 'ls':zk_list(), 'nc':zk_cmd(), 'info':zk_info(), 'par':zk_set_participant()}
        self.name = name
        self.showtxt = "[%s,id=0x]# " %(name)
    
    def parse(self, cmdline):
        try:
            cmds = cmdline.split(' ')
            param={'help':False, 'func':cmds[0], 'opt':cmds[1:]}
            if cmds[0] in ('-h', '--help'):
                param['help'] = True
            return param
        except Exception as e:
            self.log.error("parse: {0}".format(e))
    
    def getfunc(self, funcname):
        try:
            if funcname in self.funcs:
                return self.funcs[funcname]
            else:
                return None
        except Exception as e:
            self.log.error("parse: {0}".format(e))
    def auto_complete_zkpath(self, path, data):
        try:
            if len(path):
                nodes = self.zk.list_path(path)
                if len(nodes) == 1:
                    parent, child=os.path.split(path)
                    data = data.replace(path, os.path.join(parent,nodes[0])) 
                elif len(nodes) > 1:
                    self.show_list(nodes)
                else:
                    pass    
        except Exception as e:
            pass
        finally:
            return data

    def clearShowNew(self, old, new):
        if len(old):
            print(chr(27) + "[%dD" %(len(old)), end='', flush=True)
            print(chr(27) + "[K", end='', flush=True)
        print(new, end='', flush=True)
    
    def show_list(self, list):
        print('', end='\n[')
        for name in list:
            print(name, end=', ')
        print(']', flush=True)
        #print(self.showtxt, end='', flush=True)

    def showCmd(self, cmd):
        print(cmd, end='', flush=True)

    def do_exit(self, data):
        self.log.info("exit, close session 0x%x." %(self.zk.client.client_id[0]))
        self.zk.close()
        sys.exit()
    
    def do_enter(self, data):
        if len(data) == 0:
            return ''
        cmds = self.parse(data)
        if 'help' in cmds and cmds['help']:
            for func in self.funcs.values():
                func.msg()
            return ''
        func = self.getfunc(cmds['func'])
        if func is None:
            return ''
        if not self.zk.client.connected:
            self.showtxt = "[%s,s=0x%x, %s]# "%(self.name,self.zk.session_id, repr(self.zk.client.client_state))
            self.log.error("session can't servering....")
            return ''
        self.showtxt="[%s,s=0x%x]# "%(self.name, self.zk.session_id)
        try:
            func.parse(cmds['opt'])
            func.run(self.zk)
        except Exception as e:
            self.log.error("exec func[%s] error: {0}".format(e) %(cmds['func']))
        return ''

    def do_tab(self, data):
        if len(data) == 0:
            self.show_list(self.funcs)
            return data
        cmds = self.parse(data)
        if cmds['func'] in self.funcs:
            try:
                cmd = self.funcs[cmds['func']].tab(self, data)
            except Exception as e:
                self.log.error("tab func[%s] error".format(e) %(cmds['func']))
            finally:
                return cmd
        else:
            matchs = []
            for func in self.funcs:
                if re.match(cmds['func'], func):
                    matchs.append(func)
            if len(matchs) == 1:
                return matchs[0]
            else:
                self.show_list(matchs)
                return data

    def run(self):
        try:
            if not self.zk.open():
                return False
            self.showtxt="[%s,s=0x%x]# "%(self.name, self.zk.session_id)
            ioCmd = cmdInput(self.showtxt)
            cmd =''
            while True:
                type, data  = ioCmd.get(cmd, self.showtxt)
                if type not in self.keyset:
                    continue
                cmd = self.keyset[type](data)
            return True
        except Exception as e:
            self.log.error("run: {0}".format(e))
    
def help(argv, param):
    print("usage: %s -h [host] -t [timeout ms]" %(argv[0]))
    print("       -h,--host       zookeeper server host" )
    print("       -t,--timeout    timeout of session, ms\n")
    print("       exp: %s -h 127.0.0.1:9639 -t 3000" %(argv[0]))

def argv_parse(argv):
    opts, args = getopt.getopt(argv[1:], "h:t:", ["host=",'timeout='])
    param = {'timeout':15.0}
    if len(opts) == 0 and len(args):
        help(argv, param)
        return None
    for cmd, val in opts:
        if cmd in ('-h', '--host'):
            param['host'] = val
            continue
        if cmd in ('-t', '--timeout'):
            param['timeout'] = (float(val)/1000)
            continue
        help(argv, param)
        return None
    return param

def main(argv):
    try:
        param = argv_parse(argv)
        if 'host' not in param:
            help(argv, param)
            return
        t = terminal(t = param['timeout'], host=param['host'])
        if not t.run():
            help(argv, param)
    except Exception as e:
        print("main error: {0}".format(e))
    finally:
        print("exit.")

if __name__ == "__main__":
    main(sys.argv)
            
