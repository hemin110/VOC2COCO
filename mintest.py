#coding=utf-8

#author:hemin
#date:2020/3/28

import requests

import time

def main():

    while(1):
        req = requests.get("http://xxxxxxxxxx:8090/")
        time.sleep(1)
        print(req.text)



if __name__ == "__main__":
    main()