import pathlib
import pickle

from Reducer.simplifyTestcaseCore import check_effective
from Harness import Harness

"""
此文件的interesting函数是lithium在进行测试用例精简时，使用本文
"""


def interesting(argv, prefix):
    """
    从第一个文件中读取harness_result, 第二个文件中读取测试用例
    :param argv:
    :param prefix:
    :return:
    """
    harness_path = pathlib.Path(prefix).absolute().resolve().parent / "harness_result.txt"
    testcase_path = pathlib.Path(argv[0]).absolute().resolve()
    if not harness_path.exists():
        testbeds = [
            "/home/engines/hermes/hermes_0.12.0/build_release/bin/hermes -w",
            "/home/engines/quickjs/quickjs-2021-03-27/qjs",
            "/home/engines/jerryscript/jerryscript-2.4.0/build/bin/jerry",
            "/home/engines/XS/moddable-3.5.0/moddable/build/bin/lin/release/xst",
            "/home/engines/duktape/duktape-2.6.0/duk",
            "/home/engines/mujs/mujs-1.3.2/build/release/mujs"
        ]
        harness = Harness(testbeds)
        harness_path.write_bytes(pickle.dumps(harness.run_testcase(testcase_path.read_text())))
        return True
    if not testcase_path.exists():
        raise FileNotFoundError(f"文件不存在: {testcase_path}")
    harness_result = pickle.loads(harness_path.read_bytes())
    testcase = testcase_path.read_text()
    return check_effective(testcase, harness_result)[0]
