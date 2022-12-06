import logging
import sys
import pathlib

from tqdm import tqdm

from Configer import Config
import Result


sys.path.extend(['/home/yhy/EmbeddedFuzzer', '/home/yhy/EmbeddedFuzzer/src'])
logging.basicConfig(level=logging.INFO,
                    format='%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Comparision:
    def __init__(self):
        config_path = "./resources/config-experiment.json"
        self.test_case_dirs = [
            "/home/yhy/workspace/experiment/DIE",
            "/home/yhy/workspace/experiment/codeAlchemist",
            "/home/yhy/workspace/experiment/fuzzilli",
            "/home/yhy/workspace/experiment/montage",
            "/home/yhy/workspace/experiment/deepsmith"
        ]
        self.config = Config(config_path)

    def main(self):
        try:
            self.run()
        except BaseException as e:
            raise e
        finally:
            self.config.close_resources()

    def run(self):
        for case_dir in self.test_case_dirs:
            print(case_dir)
            tools_name = case_dir.split("/")[-2]
            result_dir = self.config.workspace / "uniform" / tools_name
            test_case_path_list = pathlib.Path(case_dir).rglob("*.js")
            test_case_path_list = list(test_case_path_list)
            test_case_path_list.sort()
            test_case_path_list = list(test_case_path_list)[:10000]
            print(f"test case total number is: {len(list(test_case_path_list))}")
            bug_counter = 0
            for test_case_path in tqdm(test_case_path_list):
                testcase = test_case_path.read_text()
                harness_result = self.config.harness.run_testcase(testcase)
                try:
                    # 不同测试结果存储的目录也有问题，测试时记得存储测试结果,使用pickle.dumps()将对象序序列化存储
                    # 逻辑混乱，出现异常后可能存在测试用例和执行结果，差分测试结果不对应
                    testcase = self.config.reducer.reduce(harness_result)
                    uniformed_testcase = self.config.uniform.uniform_variable_name(testcase)
                    harness_result = self.config.harness.run_testcase(testcase)
                    differential_test_result = Result.differential_test(harness_result)
                    uniformed_harness_result = self.config.harness.run_testcase(uniformed_testcase)
                    uniformed_differential_test_result = Result.differential_test(uniformed_harness_result)
                    if len(differential_test_result) == len(uniformed_differential_test_result):
                        testcase = uniformed_testcase
                        harness_result = uniformed_harness_result
                        differential_test_result = uniformed_differential_test_result
                except BaseException as e:
                    logging.warning("出bug了")
                    logging.warning(e)
                    differential_test_result = Result.differential_test(harness_result)
                if len(differential_test_result) == 0:
                    continue
                classify_id_list = []
                for info in differential_test_result:
                    bug_counter += 1
                    [classify_result, classify_id] = self.config.classifier.is_suspicious_result(info.output_id,
                                                                                                 harness_result)
                    info.classify_result = classify_result.value
                    info.classify_id = classify_id
                    classify_id_list.append(classify_id)
                classify_id_list.sort()
                classification_file = "filtered-result-" + "-".join([str(e) for e in classify_id_list])
                (result_dir / classification_file).mkdir(parents=True, exist_ok=True)
                result_path = result_dir / classification_file / (str(test_case_path).split("/"))[-1]
                result_path.write_text(testcase)
                pathlib.Path(str(result_path) + "on").write_text(str(harness_result))
            print(f"\n{'=' * 20} Bug Number: {bug_counter}{'=' * 20} ")


if __name__ == '__main__':
    try:
        Comparision().main()
    except RuntimeError:
        sys.exit(1)