import logging
import sys
import pathlib

from tqdm import tqdm

sys.path.extend([str(pathlib.Path.cwd() / "src")])

import Result
from Configer import Config
from AE import AE
from Postprocessor.callable_processor import CallableProcessor

logging.basicConfig(level=logging.INFO, format='%(message)s')


config_path = "./resources/config.json"
config = Config(config_path)

simples = AE.init_data("./test/jupyter_data/simples", "*.txt")
config.simples = simples
config.callable_processor = CallableProcessor(simples)

simple = simples[0]
logging.info(f"提取到的函数：\n{simple}")

# 测试用例生成
original_test_case = config.callable_processor.get_self_calling(simple)
logging.info(f"生成的测试用例：\n{original_test_case}")

# 测试用例变异
mutated_test_case_list = config.mutator.mutate(original_test_case, max_size=10)
mutated_test_case_list.append(original_test_case)

delimiter = "\n" + "-" * 50 + "\n"
logging.info(f"变异后的测试用例：\n{delimiter.join(mutated_test_case_list) }")

for mutated_test_case in mutated_test_case_list:
    # 执行测试用例
    harness_result = config.harness.run_testcase(mutated_test_case)
    # 模糊差分测试
    differential_test_result_list = Result.differential_test(harness_result)
    if len(differential_test_result_list) == 0:
        continue
    # 打印差分测试结果
    diff = "\n".join([str(e) for e in differential_test_result_list])
    logging.info(f"差分测试结果：\n{diff}")
    logging.info(f"触发可以结果的测试用例：\n{mutated_test_case}")
    # 打印引擎执行结果
    logging.info(f"嵌入式JavaScript引擎的执行结果：\n{harness_result}")


# 测试用例精简
cases = AE.init_data("./test/jupyter_data/simplify_testcases", "*.js")
interesting_test_cases = []
for test_case in tqdm(cases):
    harness_result = config.harness.run_testcase(test_case)
    simplified_test_case = config.reducer.reduce(harness_result)
    interesting_test_cases.append(simplified_test_case)

    logging.info("=" * 50)
    logging.info(f"精简前的测试用例:\n{test_case}")
    logging.info(f"精简后的测试用例:\n{simplified_test_case}")

# 测试结果过滤
config.classifier.clear_records()  # 精简前是否将过滤记录清空
for test_case in interesting_test_cases:
    harness_result = config.harness.run_testcase(testcase=test_case)
    differential_test_result_list = Result.differential_test(harness_result)
    suspicious_result = config.classifier.filter(differential_test_result_list, harness_result)

    logging.info("=" * 50)
    diff = "\n".join([str(e) for e in differential_test_result_list])
    logging.info(f"过滤前的测试结果：\n{diff}")
    diff = "\n".join([str(e) for e in suspicious_result])
    logging.info(f"需要手动分析的测试结果：\n{diff}")
    logging.info(f"过滤了{len(differential_test_result_list) - len(suspicious_result)}条测试结果")
