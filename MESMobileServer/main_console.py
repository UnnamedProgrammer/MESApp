import logging
import os
from datetime import datetime
from Controls.Server import Server


fdir = os.path.dirname(__file__) + "\\logs\\"
if os.path.exists(fdir):
    filename = r'Log_at_'+datetime.strftime(datetime.now(),'%Y-%m-%d %H-%M-%S')+'.log'
    os.path.join(fdir,filename)
    open(fdir+filename, 'w',encoding="utf-8")
else:
    os.mkdir(os.path.dirname(__file__) + "\\logs")
    filename = r'Log_at_'+datetime.strftime(datetime.now(),'%Y-%m-%d %H-%M-%S')+'.log'
    os.path.join(fdir,filename)
    open(fdir+filename, 'w',encoding="utf-8")
    
file_log = logging.FileHandler(fdir+filename)
console_out = logging.StreamHandler()


logging.basicConfig(handlers=(file_log, console_out), 
                    format='[%(asctime)s | %(levelname)s]: %(message)s', 
                    datefmt='%m.%d.%Y %H:%M:%S',
                    level= logging.DEBUG,
                    encoding='utf-8')

Serv = Server()
Serv.ServerRun()
