from threading import Thread
from time import sleep
import os

def function(i):
    #i = args[0]
    name = 'm_topo_thr_' + str(i) 
    os.system('touch ' + name)
    with open(name, "w") as file:
        file.write("Thread " + str(i))

if __name__ == "__main__":
    threads = []
    for i in range(1,5):
        thread = Thread(target=function, args = (i,))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished work!'


