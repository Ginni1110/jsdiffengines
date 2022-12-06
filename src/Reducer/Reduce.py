import math
import logging

import Result
from Reducer import reduce_by_line, simplifyTestcaseCore
from utils.JSASTOpt import build_ast, generate_es_code
import jsbeautifier


class Reducer:
    def __init__(self, multi_threads: bool = True):
        self.test_case_ast = None
        self.harness_result = None
        self.multi_threads = multi_threads

        # 在删除代码行对测试用例进行精简时可能会触发bug
        self.mutated_harness_result_list = None

    def reduce(self, harness_result: Result.HarnessResult) -> str:
        """
        精简测试用例，删除测试用例中与触发js引擎bug无关的语句
        :param harness_result:各个引擎执行未精简测试用例的执行结果
        :return: 返回精简后的测试用例。若无法精简，则返回精简前的测试用例。
        """
        self.harness_result = harness_result
        self.mutated_harness_result_list = []  # 每个测试用精简前都需要清零
        original_test_case = harness_result.testcase.strip()
        try:
            self.test_case_ast = build_ast(original_test_case)
        except Exception as r:
            # 当测试用例无法提取抽象语法树时,则使用基于代码行的方式进行精简
            logging.info("Failed to extract AST. ")
            [simplified_test_case, new_bugs_list] = reduce_by_line.simple_by_statement(harness_result)
            self.mutated_harness_result_list = new_bugs_list
            return self.beautify_test_case(simplified_test_case)

        self.traverse(self.test_case_ast)  # 按代码块进行删除
        self.peeling(self.test_case_ast)  # 剥开代码中的外层语句块
        return generate_es_code(self.test_case_ast)

    def traverse(self, node: dict, lithium_algorithm=True):
        """
        精简测试用例，删除测试用例中与触发js引擎bug无关的语句
        :param node: traversed_node无法被删除，但其子节点可能被精简。此函数主要对其子节点进行精简
        :param lithium_algorithm: 是否启用ddmin算法对每一层的节点进行删除
        """
        # 逆序遍历字典，是为了保证在对函数进行精简时，先精简函数体再精简函数。
        for key, values in reversed(list(node.items())):
            # if type(v) == list and k != "arguments" and k != "params":
            if type(values) == list:
                # 变量声明至少得有一个节点，否则一定会出现语法错误。此处只能是0或1，若修改请就修改后续的ddmin中的代码
                remained = 1 if key == "declarations" else 0
                # 尝试使用ddmin对每一层节点进行精简
                if lithium_algorithm:
                    self.ddmin(values, remained)
                else:
                    # 尝试删除所有子节点
                    if len(values) > 1:
                        node[key] = []
                        [removable, new_bug] = self.removable()
                        if new_bug is not None:
                            self.mutated_harness_result_list.append(new_bug)
                        if removable:
                            continue
                        else:
                            # 恢复删除前的测试用例
                            node[key] = values
                    # 对其中的部分节点进行删除
                    for index in range(len(values) - 1, -1, -1):
                        # 这里可以考虑使用二分法进行删除，删除1，1/2，1/4
                        tmp_node = values.pop(index)
                        [removable, new_bug] = self.removable()
                        if new_bug is not None:
                            self.mutated_harness_result_list.append(new_bug)
                        if removable:
                            continue
                        else:
                            # 恢复测试用例
                            values.insert(index, tmp_node)
                            # 对其子节点进行精简
                            self.traverse(tmp_node)
            elif type(values) == dict and key != "loc":
                self.traverse(values)  # 对其子节点进行精简

    def ddmin(self, arr: list, remained: int):
        """

        :param arr: 尝试对数组中元素进行精简
        :param remained: 当前节点列表中至少保留的节点数
        :return:
        """
        size = len(arr)
        if size == 0:
            return
        chunk_size = 2 ** int(math.log2(size))
        while chunk_size >= 1:
            # 拆分为大小为chunk_size的块的数量
            size = len(arr)
            for index in range(size - chunk_size, -1, -chunk_size):
                if len(arr) <= remained:  # 只有一个节点且需要至少保留一个节点
                    self.traverse(arr[index])
                    return
                logging.debug(f"尝试删除的节点：{index} - {index + chunk_size}")
                tmp_deleted = multi_pop(arr, index, index + chunk_size)
                [removable, new_bug] = self.removable()
                if new_bug is not None:
                    self.mutated_harness_result_list.append(new_bug)
                if not removable:  # 可疑删除
                    multi_push(arr, index, tmp_deleted)
                    # 当删除的节点数量为1且当前节点无法进行删除时，则对其子节点进行删除
                    if chunk_size == 1:
                        self.traverse(arr[index])
            chunk_size = chunk_size >> 1

    def peeling(self, test_case_ast: dict):
        """
        删除代码中无效的外壳，如无用的外层循环。具体的精简算法与给用例语句添加循环的算法相反。
        :param test_case_ast: 待精简的测试用例的AST树
        :return: 精简后
        """
        queue = [test_case_ast]
        while len(queue) > 0:
            node = queue.pop(0)
            # 遍历抽象语法树
            for key, value in node.items():
                if key == 'type' and value == "VariableDeclaration":
                    for dec in node["declarations"]:
                        if not dec["init"] is None and dec["init"]["type"] == "FunctionExpression":
                            queue.append(dec["init"]["body"])
                elif type(value) == list and key == "body":
                    child_node_list = value
                    for index in range(len(child_node_list) - 1, -1, -1):
                        # 对测试用例进行剥壳
                        # 此处只剥变异添加的循环，其余的后续更新
                        tmp_node = child_node_list[index]
                        try:
                            if tmp_node["type"] == "ForStatement" \
                                    and tmp_node["init"]["declarations"][0]["id"]["name"] == "INDEX":
                                # 我们添加for循环时，循环体中一条语句，因此此处不需要用循环
                                child_node_list[index] = tmp_node["body"]["body"][0]
                                removable = self.removable()[0]
                                if removable:
                                    return
                                else:
                                    # 恢复用例
                                    child_node_list[index] = tmp_node
                        except BaseException as e:
                            child_node_list[index] = tmp_node
                            pass
                        queue.append(child_node_list[index])
                elif type(value) == dict and key != "loc":
                    queue.append(value)

    def removable(self):
        """
        判断测试用例是否可以精简
        :return: 测试用例的删除是否有效
        """
        try:
            tmp_code = generate_es_code(self.test_case_ast)
        except BaseException as e:
            return [False, None]
        return simplifyTestcaseCore.is_removable(self.harness_result, tmp_code)

    @staticmethod
    def beautify_test_case(test_case: str) -> str:
        """
        美化精简后的测试用例，使其可读性更强
        :param test_case:
        :return:
        """
        beautified_test_case = str(test_case).split("\n")
        for index in range(len(beautified_test_case) - 1, -1, -1):
            if beautified_test_case[index].strip() == '':
                beautified_test_case.pop(index)
        beautified_test_case = "\n".join(beautified_test_case)
        return jsbeautifier.beautify(beautified_test_case)


def multi_pop(arr: list, start: int, end: int):
    deleted_arr = []
    for num in range(end - start):
        deleted_arr.append(arr.pop(start))
    return deleted_arr


def multi_push(arr: list, start: int, to_added: list):
    for tmp_index in range(len(to_added) - 1, -1, -1):
        arr.insert(start, to_added[tmp_index])
