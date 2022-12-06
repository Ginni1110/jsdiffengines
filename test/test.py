import json
import pathlib
from Configer import Config
from Reducer.Reduce import Reducer
from Result import differential_test

#
testcase = (pathlib.Path.cwd() / "test/case.js").absolute().resolve().read_text()

# 获取输出结果
config_path = "./resources/config.json"
config = Config(config_path)
# config.init_data()
result = config.harness.run_testcase(testcase)
reducer = Reducer()
simplified_test_case = reducer.reduce(result)
# simplified_result = config.harness.run_testcase(simplified_test_case)
# # simplified_bug_info = differential_test(simplified_result)
# # # bug_info = differential_test(result)
# # # print(result)
# # # print(json.dumps([e.serialize() for e in bug_info], indent=4))
# # print(simplified_result)
# # print(json.dumps([e.serialize() for e in simplified_bug_info], indent=4))
# # print(simplified_test_case)
# # config.database.query_mutated_test_case()