import logging
import sys

from tqdm import tqdm

sys.path.extend(['/home/yhy/EmbeddedFuzzer', '/home/yhy/EmbeddedFuzzer/src'])
from Configer import Config
import Result
from utils import crypto

logging.basicConfig(level=logging.INFO,
                    format='%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Fuzzer:
    def __init__(self):
        config_path = "./resources/config.json"
        self.config = Config(config_path)
        self.config.init_data()

    def main(self):
        try:
            self.run()
        except BaseException as e:
            raise e
        finally:
            self.config.close_resources()

    def run(self):
        for simple in tqdm(self.config.simples, ncols=100):
            original_test_case = self.config.callable_processor.get_self_calling(simple)
            # self.config.database.update_simple_status(simple)  # 将这个函数标记过已经被使用过了，不会重复测试
            mutated_test_case_list = self.config.mutator.mutate(original_test_case, max_size=20)
            mutated_test_case_list.append(original_test_case)
            for mutated_test_case in mutated_test_case_list:
                harness_result = self.config.harness.run_testcase(mutated_test_case)
                differential_test_result = Result.differential_test(harness_result)
                if len(differential_test_result) == 0:
                    continue
                simplified_test_case = self.config.reducer.reduce(harness_result)
                uniformed_test_case = self.uniform(simplified_test_case)
                new_harness_result = self.config.harness.run_testcase(uniformed_test_case)
                suspicious_differential_test_result_list = self.config.classifier.filter(
                    Result.differential_test(new_harness_result), new_harness_result)
                if len(suspicious_differential_test_result_list) == 0:  # 没有可疑的测试结果需要分析
                    continue
                self.save_interesting_test_case(uniformed_test_case)

    def uniform(self, test_case: str) -> str:
        """
        规范化用例。规范化测试用例的变量名，如果变量名替换前后测试结果不变，则返回规范化后的测试用例；否则返回原始的测试用例
        :param test_case: 原始测试用例
        :return: 规范化后的测试用例
        """
        try:
            uniformed_test_case = self.config.uniform.uniform_variable_name(test_case)
            original_harness_result = self.config.harness.run_testcase(test_case)
            uniformed_harness_result = self.config.harness.run_testcase(uniformed_test_case)
            # 这里只简单比较变量替换后的测试用例触发的可疑测试结果的数量是否相同
            if len(Result.differential_test(original_harness_result)) == len(Result.differential_test(
                    uniformed_harness_result)):
                return uniformed_test_case
        except BaseException as e:
            pass
        return test_case

    def save_interesting_test_case(self, test_case: str):
        """
        将可能触发缺陷的测试用例进行存储，便于分析
        :param test_case: 可疑的测试用例
        """
        hash_code = crypto.md5_str(test_case)  # 计算测试用例的哈希值
        file_path = (self.config.workspace / f"interesting_testcase/{hash_code}.js").absolute().resolve()  # 设置测试用例的存储路径
        file_path.parent.mkdir(parents=True, exist_ok=True)  # 创建文件存储的文件夹
        logging.info(f"\nInteresting test case is writen to the file:\n {file_path}")
        file_path.write_text(test_case)  # 存储测试用例


if __name__ == '__main__':
    try:
        Fuzzer().main()
    except RuntimeError:
        sys.exit(1)
