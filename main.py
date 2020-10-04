from multiprocessing import Pool
from multiprocessing import Process

from transfer import read_com
from config import  PORT_INFO

# print (list(PORT_INFO.keys()))
if __name__ == '__main__':
    # pool = Pool()                         # Create a multiprocessing Pool
    # pool.map(read_com, list(PORT_INFO.keys()))  # process data_inputs iterable with pool
    processes = []
    for com in PORT_INFO.keys():
        print (com)
        p = Process(target=read_com, args=(com,))
        processes.append(p)

    for p in processes:
        p.start()
