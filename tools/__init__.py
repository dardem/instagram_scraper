def write_log(mess):
    with open('log/log.txt', 'a') as f:
        f.write(mess)