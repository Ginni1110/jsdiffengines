import copy
import logging
from typing import List

from utils.JSASTOpt import *
from Mutator.unexecutedCodeDeletion import CodeRemover


class Timer:
    def __init__(self, start: dict, end: dict, output: dict):
        self.start_timer_js_ast = start
        self.end_timer_js_ast = end
        self.output_js_ast = output


class Mutator:
    def __init__(self, engine: str = "node", max_size: int = 30):
        self.loop_structure_ast_template = self.get_loop_structure_ast(1000)
        self.timer_template = self.get_plug_in_timer()
        self.codeRemover = CodeRemover(engine)
        self.max_size = max_size  # 变异后测试用例的最大数量

    def mutate(self, test_case_code: str, max_size: int = 30) -> List[str]:
        """
        对测试用例进行变异，获取变异后的测试用例集合。
        :param test_case_code:
        :param max_size: 最大的变异的测试用例数量
        :return:变异后的测试用例，不包括编译前的测试用例
        """
        self.max_size = max_size
        # 删除测试用例中没有被执行到的语句，减少变异后出现大量“相同”的测试用例。
        try:
            test_case_ast = build_ast(test_case_code)
        except BaseException as e:
            # 无法提取抽象语法树，不进行精简
            logging.debug(f"Failed to extract AST.\n {str(e)}")
            return []
        optimized_test_case_ast = self.codeRemover.delete_useless_code(test_case_ast)
        return self.add_loop_surrounding_statement(optimized_test_case_ast)

    def add_loop_surrounding_statement(self, test_case_ast: dict) -> List[str]:
        mutated_test_case_list = []
        loop_type = {'ForStatement', 'ForInStatement', 'WhileStatement', 'ForOfStatement', 'DoWhileStatement'}
        if len(test_case_ast["body"]) == 0:
            return mutated_test_case_list
        queue = [test_case_ast]
        while len(queue) > 0:
            node = queue.pop(0)
            for key, value in node.items():
                if key == 'type' and loop_type.__contains__(value):
                    break
                if key == 'type' and value == "VariableDeclaration":
                    for dec in node["declarations"]:
                        if not dec["init"] is None and dec["init"]["type"] == "FunctionExpression":
                            node = dec["init"]["body"]
                            queue.append(node)
                elif type(value) == list and key == "body":
                    child_node_list = value
                    for index in range(len(child_node_list)):  # 都每条语句进行变异，增加这条语句执行时间占总的执行时间的比例
                        queue.append(child_node_list[index])
                        node_list_deepcopy = copy.deepcopy(child_node_list)
                        node_list_deepcopy = self.add_loop(node_list_deepcopy, index)
                        node[key] = node_list_deepcopy
                        mutated_test_case = generate_es_code(copy.deepcopy(test_case_ast))  # 根据ast生成代码
                        mutated_test_case_list.append(mutated_test_case)
                        node[key] = child_node_list  # 恢复AST
                        if len(mutated_test_case_list) >= self.max_size:
                            return mutated_test_case_list
                elif type(value) == dict and key != "loc":
                    queue.append(value)
        return mutated_test_case_list

    def add_loop(self, node_list: list, index: int) -> list:
        """
        给node_list中第index条语句外包一层循环
        :param node_list: 需要添加计时器的语句所在块中的所有语句列表
        :param index: 需要添加计时器的语句索引
        :return: 添加循环后的node_list
        """
        loop_wrapped_node = copy.deepcopy(self.loop_structure_ast_template)
        loop_wrapped_node["body"]["body"].append(node_list[index])
        node_list[index] = loop_wrapped_node
        return node_list

    def add_timer(self, node_list: list, index: int) -> list:
        """
        给node_list中的第index条语句添加计时器
        :param node_list: 需要添加计时器的语句所在块中的所有语句列表
        :param index: 需要添加计时器的语句索引
        :return: 添加计时器的node_list
        """
        node_list.insert(index + 1, self.timer_template.output_js_ast)
        node_list.insert(index + 1, self.timer_template.end_timer_js_ast)
        node_list.insert(index, self.timer_template.start_timer_js_ast)
        return node_list

    @staticmethod
    def get_loop_structure_ast(cycles: int):
        """
        获取循环结构的抽象语法树，用于改变测试用例中语句的执行次数
        :param cycles: 循环语句的执行次数
        :return: 循环结构的抽象语法树
        """
        code = """for (var INDEX=0; INDEX<10; INDEX++) {}
        """
        ast = build_ast(code)
        loop_structure_ast = ast["body"][0]
        loop_structure_ast["test"]["right"]["value"] = cycles
        return loop_structure_ast

    @staticmethod
    def get_plug_in_timer() -> Timer:
        """
        获取计时器开始，结束，和输出三条语句的抽象语法树
        :return:
        """
        code = """
        var startTimestamp = (new Date()).getTime();
        var endTimestamp = (new Date()).getTime();
        print("EmbeddedFuzzerTimer:" + (endTimestamp - startTimestamp) + "ms");
        """
        ast = build_ast(code)
        return Timer(ast["body"][0], ast["body"][1], ast["body"][2])
