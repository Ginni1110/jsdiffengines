import math

import Result
from Harness import Harness
from ResultFilter import classify


def check_effective(testcase: str, before_harness_result: Result.HarnessResult):
    """
    再次拆分成两个函数，一个函数直接比较两个引擎执行结果是否相同

    :param testcase: 精简后的测试用例
    :param before_harness_result: 精简前测试用例的harnessResult
    :return: [是否可以精简, 精简后触发的新bug的harnessResult], 若没有发现新bug则返回None
    """
    before_bug_info = Result.differential_test(before_harness_result)

    testbeds = [output.testbed for output in before_harness_result.outputs]
    harness = Harness(engines=testbeds)
    after_harness_result = harness.run_testcase(testcase)

    # 修正output_id，便于进行差分测试。若不修正，则差分测试结果无法与引擎一一对应
    after_harness_result = rectify_output_id(before_harness_result, after_harness_result)
    after_bug_info = Result.differential_test(after_harness_result)
    # import json
    # print("\n\n====================================\n\n")
    # print(testcase)
    # print(json.dumps([e.serialize() for e in bug_info], indent=4))
    # print(harness_result)
    # 确保精简前后引擎的bug数量不一致
    if len(after_bug_info) != len(before_bug_info):
        return [False, after_harness_result if len(after_bug_info) > 0 else None]

    # 确保精简前后异常的引擎一一对应（output_id 一一对应即可）
    before_suspicious_id_set = set([e.output_id for e in before_bug_info])
    after_suspicious_id_set = set([e.output_id for e in after_bug_info])
    if len(before_suspicious_id_set.union(after_suspicious_id_set)) > len(before_suspicious_id_set):
        return [False, after_harness_result]

    # 判断精简前后引擎的输出类型是否相同
    testbed_output_class_dict = {output.testbed: output.output_class for output in before_harness_result.outputs}
    for output in after_harness_result.outputs:
        if not testbed_output_class_dict[output.testbed] == output.output_class:
            return [False, after_harness_result]

    # 精简前后得到的bug类型要相同
    before_output_id_bug_ype_dict = {e.output_id: e.bug_type for e in before_bug_info}
    for info in after_bug_info:
        if not before_output_id_bug_ype_dict[info.output_id] == info.bug_type:
            return [False, after_harness_result]

    # 关键异常信息需要一致，这里的关键异常信息不能标准化

    # 针对性能问题的测试结果进行精简,精简后引擎之间的性能问题只能被放大。若性能差距被缩小则不允许进行精简。这里的差距指的时比率
    performance_output_id = set([e.output_id for e in after_bug_info if e.bug_type == "Performance issue"])
    if len(performance_output_id) > 0:
        [before_suspicious_outputs, before_normal_outputs] = split_output(before_harness_result)
        before_shortest_time = min([output.duration_ms for output in before_normal_outputs])
        before_id_duration_dict = {output.id: output.duration_ms
                                   for output in before_harness_result.outputs if
                                   performance_output_id.__contains__(output.id)}
        # 因为计时器的精度在15ms左右，为了避免误差的影响。需要的原始的测试结果的性能差降低（向下取整）
        before_testbeds_gap_dict = {bed: math.floor(duration / before_shortest_time) for bed, duration in
                                    before_id_duration_dict.items()}

        [after_suspicious_outputs, after_normal_outputs] = split_output(after_harness_result)
        after_shortest_time = min([output.duration_ms for output in after_normal_outputs])
        after_id_duration_dict = {output.id: output.duration_ms
                                  for output in after_harness_result.outputs if
                                  performance_output_id.__contains__(output.id)}
        after_testbeds_gap_dict = {bed: (duration / after_shortest_time) for bed, duration in
                                   after_id_duration_dict.items()}
        for bed, gap in before_testbeds_gap_dict.items():
            if after_testbeds_gap_dict[bed] < gap:  # 精简后性能差距变小
                return [False, None]

    return [True, None]


def rectify_output_id(before_harness_result: Result.HarnessResult,
                      after_harness_result: Result.HarnessResult) -> Result.HarnessResult:
    """
    将用例精简前执行结果的output_id赋值给精简后对应引擎的output_id
    :param before_harness_result: 精简前引擎的执行结果
    :param after_harness_result: 精简后引擎的执行结果、
    :return: 纠正后的执行结果
    """
    engine_id_dict = {output.testbed: output.id for output in before_harness_result.outputs}
    for output in after_harness_result.outputs:
        output.id = engine_id_dict[output.testbed]
    return after_harness_result


def split_output(result: Result.HarnessResult):
    """
    将所有的输出拆分为可疑的（可能说是bug）和输出正常的
    :param result:
    :return:
    """
    # 此处不重新进行差分测试会导致bug，原因：由于过滤导致的从数据库中读取的测试结果不一定是差分测试后的所有不一致的全部结果
    differential_result_output_ids = [info.output_id for info in Result.differential_test(result)]
    suspicious_output_ids_set = set(differential_result_output_ids)
    suspicious_output = []
    normal_output = []
    for output in result.outputs:
        if suspicious_output_ids_set.__contains__(output.id):
            suspicious_output.append(output)
        else:
            normal_output.append(output)
    return [suspicious_output, normal_output]


def is_removable(harness_result: Result.HarnessResult, code: str):
    return check_effective(code, harness_result)


def get_key_outputs(output: Result.Output):
    """
    返回lithium能识别的关键报错信息或输出
    :param output:
    :return:
    """
    key_outputs = classify.list_essential_exception_message(output.stderr + output.stdout)
    if key_outputs == "":
        key_outputs = output.stdout
    return key_outputs
