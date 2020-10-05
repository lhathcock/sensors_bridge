from multiprocessing import Process
from transfer import read_com, connect_to_server, send_temp_files
from config import PORT_INFO

connect_to_server()
if __name__ == '__main__':
    processes = []
    for com in PORT_INFO.keys():
        print(com)
        p = Process(target=read_com, args=(com,))
        processes.append(p)
    p2 = Process(target=send_temp_files)
    processes.append(p2)

    for p in processes:
        p.start()
