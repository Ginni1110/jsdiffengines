from typing import List

from Reducer import simplifyTestcaseCore
import Result


def simple_by_statement(init_result: Result.HarnessResult):
    """
    精简成功则返回精简后的测试用例，否则返回None
    :param init_result:
    :param optimization:
    :param multi_threads:
    :param with_output_info:
    :return: [simplified test case, List[Result.HarnessResult]]
    """
    new_bug_harness_result_list = []
    original_test_case = init_result.testcase.strip()
    # 直接将list的变量名赋值给变量时，是将list的引用赋值给变量
    test_case_last_list = original_test_case.split("\n")  # 上一轮精简后的测试用例
    tmp_test_case_list = test_case_last_list[:]  # 遍历一行语句就可能改变，改变条件是能精简
    loop_counter = 0
    # 为什么只进行两轮精简的原因：参考lithium的精简算法
    for index in range(2):
        loop_counter += 1
        # print(f"第{loop_counter}轮精简")
        for row in range(len(tmp_test_case_list) - 1, -1, -1):  # 从后向前简化能够减少迭代的次数
            tmp = tmp_test_case_list[:]
            # print(f"正在精简第{row+1}行")
            tmp.pop(row)
            [removable, new_bug] = simplifyTestcaseCore.is_removable(init_result, "\n".join(tmp))
            if new_bug is not None:
                new_bug_harness_result_list.append(new_bug)
            if removable:
                # print(f"第 {row+1} 成功的被精简")
                tmp_test_case_list = tmp[:]  # 简化成功
        if len(test_case_last_list) == len(tmp_test_case_list):  # 已经无法精简了
            # 这一轮无法被精简，下一轮也不可能被精简
            break
        test_case_last_list = tmp_test_case_list[:]
        # print(f"第 {loop_counter} 轮精简有效")
    reduced_test_case = "\n".join(test_case_last_list)
    return [reduced_test_case, new_bug_harness_result_list]
