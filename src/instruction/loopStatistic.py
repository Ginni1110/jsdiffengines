import logging

import tqdm
import pathlib

# from Reducer.reduce_by_block import *
from db.db_operation import DBOperation
from utils.JSASTOpt import build_ast

logging.basicConfig(level=logging.INFO,
                    format='%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
LOOPTYPE = ["WhileStatement", "DoWhileStatement", "ForStatement", "ForInStatement", "ForOfStatement"]


def get_loop_statement_num(testcase: str) -> dict:
    loop_num = dict()
    try:
        ast = build_ast(testcase)
    except Exception as r:
        # 当测试用例无法提取抽象语法树时,则使用基于代码行的方式进行精简
        logging.debug("Failed to extract AST. ")
    else:
        loop_num = count_loop(ast)
    return loop_num


def count_loop(ast: dict):
    counter_dict = dict(zip(LOOPTYPE, [0 for e in range(len(LOOPTYPE))]))  # 存放统计结果的字典
    queue = [ast]
    type_set = set(LOOPTYPE)
    while len(queue) > 0:
        node = queue.pop(0)
        for k, v in node.items():
            if k == 'type' and type_set.__contains__(v):  # 判断是否是循环结构
                counter_dict[v] = counter_dict[v] + 1  # 统计循环结构
            if str(type(v)) == "<class 'list'>" and k != "arguments" and k != "params":
                child_node_list = v
                for childNode in child_node_list[::-1]:
                    if childNode is not None:
                        queue.append(childNode)
            elif str(type(v)) == "<class 'dict'>" and k != "loc":
                queue.append(v)
    return counter_dict


def union_dict(*objs):
    _keys = set(sum([list(obj.keys()) for obj in objs], []))
    _total = {}
    for _key in _keys:
        _total[_key] = sum([obj.get(_key, 0) for obj in objs])
    return _total


def sum_dict_value(dic: dict) -> int:
    count = 0
    for k, v in dic.items():
        count += v
    return count


def main(db_path: str):
    db = DBOperation(db_path)
    counter_dict = dict()
    delimiter = "\n\n\n==============================================================\n\n\n"
    content = ""
    simple_num = 0
    try:
        db = DBOperation(db_path)
        simple_list = db.query_corpus(unused_only=False)
        # simple_list = [(pathlib.Path.cwd() / "test/data/loop-statistic-testcase.js").read_text()]
    finally:
        db.close()
    try:
        for simple in tqdm.tqdm(simple_list):
            simple_count = get_loop_statement_num(simple)
            counter_dict = union_dict(counter_dict, simple_count)
            if sum_dict_value(simple_count) > 0:  # 如果有循环结构，则保存这个simple
                content += f"simple {simple_num + 1}:\n" + str(simple_count) + "\n" + simple + delimiter
                simple_num += 1
    finally:
        p = pathlib.Path.cwd() / (db_path.split("/")[-1][:-3] + ".txt")
        p.write_text(content)
        print(counter_dict)


if __name__ == '__main__':
    db_path_top = "/home/yhy/workspace/top2000corpus-20200410-FX-SF.db"
    db_path_bottom = "/home/yhy/data/bottom2000corpus-20200412-FX-SF.db"
    # logging.info("Top 2000 repositories:")
    # main(db_path_top)
    logging.info("Bottom 2000 repositories:")
    main(db_path_bottom)