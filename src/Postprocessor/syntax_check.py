import os
import subprocess
import re


def file_split(file_path):
    """
    将一整个生成的文件
    :param file_path:文件路径
    """
    # 读文件，得到 list
    with open(file_path, 'r', encoding='utf-8') as RawFile:
        content = RawFile.read()
        list = re.split('-------------------------------------', content)

    # js_list = ["var a = " + i.strip() for i in list]
    js_list = [("var a = " + i).strip().replace('\n', '') for i in list]

    return js_list


def syntax_check(file_path):
    """
    通过uglifyjs对JS语料库进行预处理，包括去注释、变量名替换、压缩
    遇到有语法错误的文件会报错，利用这个特性删除包含语法错误的代码
    """
    cmd = ['uglifyjs', file_path, '-o', file_path]

    # p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    # 下面这行注释针对Windows本地
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
    if ((p.poll() is None) and p.stderr.readline().__len__() > 0 and os.path.exists(file_path)) or not os.path.getsize(
            file_path):
        return False
    return True


if __name__ == "__main__":

    # file_path = input()   # 这里指定要进行测试的文件
    file_path = './FORYHY/FORYHYList1/'   # 这里指定要进行测试的文件
    count = 0
    # js_list = file_split(file_path)

    right = 0
    false = 0

    for root, dirs, files in os.walk(file_path):
        for file in files:
            if count % 50 == 0:
                print("当前处理到:",count)
            if syntax_check(file_path + file):
                right += 1
                print(count)
            else:
                false += 1
            count += 1

    print('right:' + str(right))
    print('false:' + str(false))


    # for idx, i in enumerate(js_list):
    #
    #     if idx % 50 == 0:
    #         print("当前处理到：", idx)
    #
    #     with open('temp.js', 'w', encoding='utf-8') as f:
    #         f.write(i)
    #
    #     if syntax_check('temp.js'):
    #         right += 1
    #         print(right)
    #     else:
    #         false += 1
    #
    # print('right:' + str(right))
    # print('false:' + str(false))
    #
    # os.remove('temp.js')
