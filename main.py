from multiprocessing import Process
from transfer import read_com,create_log, connect_to_server, send_temp_files, connect_to_lan_via_socket
from config import PORT_INFO


if __name__ == '__main__':
    processes = []
    for com in PORT_INFO.keys():
        # print(com)
        msg = 'Sensors Bridge connected to {} ({})'.format(
            PORT_INFO[com]['name'], com
        )
        msg_with_time = create_log(msg)
        print(msg_with_time)
        connect_to_server(com)

        p = Process(target=read_com, args=(com,))
        processes.append(p)
    # p2 = Process(target=send_temp_files)
    # processes.append(p2)

    for p in processes:
        p.start()
