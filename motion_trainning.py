# -*- coding: utf-8 -*-
#
# by oldj
# http://oldj.net/
#
 

import time
import pythoncom
import pyHook
from datetime import datetime


now = datetime.now()
log_file_name = "motion_%s_%s_%s.log" % (now.year, now.month, now.day)
output_file = open(log_file_name, "a")
 
def onMouseEvent(event):
    if event.Message == 512:  # not tracking mouse move
        return True

    print event.Message, event.Position
    msg = "%s|%s|%s|%s|%s|%s|%s|%s\n" % (
                                        time.time(),
                                        event.MessageName, 
                                        event.Message,
                                        event.Window,
                                        event.WindowName,
                                        event.Position,
                                        event.Wheel,
                                        event.Injected)
    output_file.write(msg)
 
    # 返回 True 以便将事件传给其它处理程序
    # 注意，这儿如果返回 False ，则鼠标事件将被全部拦截
    # 也就是说你的鼠标看起来会僵在那儿，似乎失去响应了
    return True
 
def onKeyboardEvent(event):
    # 监听键盘事件
    print event.Message, event.Key
    
    msg = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" % (
                                        time.time(),
                                        event.MessageName, 
                                        event.Message,
                                        event.Window,
                                        event.WindowName,
                                        event.Ascii,
                                        event.Key,
                                        event.KeyID,
                                        event.ScanCode,
                                        event.Extended,
                                        event.Injected,
                                        event.Alt,
                                        event.Transition)
    output_file.write(msg)
 
    # 同鼠标事件监听函数的返回值
    return True
 
def main():
    # 创建一个“钩子”管理对象
    hm = pyHook.HookManager()
 
    # 监听所有键盘事件
    hm.KeyDown = onKeyboardEvent
    # 设置键盘“钩子”
    hm.HookKeyboard()
 
    # 监听所有鼠标事件
    hm.MouseAll = onMouseEvent
    # 设置鼠标“钩子”
    hm.HookMouse()
 
    # 进入循环，如不手动关闭，程序将一直处于监听状态
    pythoncom.PumpMessages()
 
if __name__ == "__main__":
    main()
    output_file.close()
