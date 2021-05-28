import win32com.client
import sys
shell = win32com.client.Dispatch("WScript.Shell")
shell.Run('"C:/Program Files (x86)/teraterm/ttermpro.exe" /C=4, /BAUD=19200')
# shell.Run('"C:\\Program Files (x86)\\teraterm\\ttermpro.exe"'
#           )
# shell.AppActivate("COM4:19200baud - Tera Term VT")
# shell.SendKeys("1")

# shell.AppActivate("COM1"
#                   ":12900baud - Tera Term VT")
# shell.SendKeys("{Enter}")
# output = subprocess.Popen(["C:\\Program Files (x86)\\teraterm\\ttermpro.exe",'/C=4','/BAUD=115200'], stdout=subprocess.PIPE)
# print(vars(output))

from win32com.client import GetObject
# from datetime import datetime
import os
import time
time.sleep(10)
WMI = GetObject('winmgmts:')
for process in WMI.ExecQuery('select * from Win32_Process where Name="ttermpro.exe"'):
    print("Terminating PID:", process.ProcessId)
    os.system("taskkill /pid " + str(process.ProcessId))
