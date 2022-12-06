import random
import pathlib
import subprocess
import tempfile
import logging
import json

from Reducer import simplifyTestcaseCore
import Result


def simplify_with_lithium(result: Result.HarnessResult):
    """
    精简成功则返回精简后的测试用例，否则返回原始用例
        1. 若两类引擎中的其中一类精简成功，则选取精简成功的那个。
        2. 若两类都没有精简成功（没有精简或精简出错），则选取异常引擎的精简结果。
    :param result:
    :param optimization:
    :return:
    """
    testcase = result.testcase.strip()
    [suspicious_outputs, normal_outputs] = simplifyTestcaseCore.split_output(result)
    if len(suspicious_outputs) == 0 or len(normal_outputs) == 0:
        return testcase
    candidate = [random.choice(suspicious_outputs), random.choice(normal_outputs)]
    try:
        with tempfile.NamedTemporaryFile(prefix="javascriptTestcase_", suffix=".js", delete=True) as f:
            testcase_path = pathlib.Path(f.name)
            # 获取lithium能识别的关键报错信息
            candidate_simplified_testcase = None
            for output in candidate:
                testcase_path.write_bytes(bytes(testcase, encoding="utf-8"))
                simplify_core(output, testcase_path)
                simplified_testcase = testcase_path.read_text()
                # 偏重于选有问题的引擎的精简结果
                if candidate_simplified_testcase is None:
                    candidate_simplified_testcase = simplified_testcase
                if simplified_testcase != testcase and \
                        simplifyTestcaseCore.check_effective(simplified_testcase, result)[0]:  # 精简成功
                    candidate_simplified_testcase = simplified_testcase
                    break
    except BaseException as e:
        logging.warning(e)
        return testcase
    return candidate_simplified_testcase if candidate_simplified_testcase is not None else testcase


def simplify_core(output: Result.Output, testcase_path: pathlib.Path):
    """
    lithium的执行方式：python -m lithium outputs "关键的输出信息" 引擎的执行命令 测试用例文件
    :param output:
    :param testcase_path:
    :return:
    """
    # 删除输出信息中的末尾的换行符，这会影响精简的效果
    key_outputs = simplifyTestcaseCore.get_key_outputs(output).strip()
    key_outputs = json.dumps(key_outputs, ensure_ascii=True)
    command = f"/root/anaconda3/bin/python -m lithium outputs {key_outputs} " \
              f"{output.testbed} {str(testcase_path)}"
    print(command)
    pro = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, shell=True)
    stdout, stderr =pro.communicate()
    # print(stdout)
    # print(stderr)
