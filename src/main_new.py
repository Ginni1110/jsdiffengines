import json
import logging
import sys
import time

from tqdm import tqdm

import Result
from Configer import Config
from utils import labdate, crypto

sys.path.extend(['/home/yhy/EmbeddedFuzzer', '/home/yhy/EmbeddedFuzzer/resources', '/home/yhy/EmbeddedFuzzer/src'])
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
        for simple in tqdm(self.config.simples):
            original_test_case = self.config.callable_processor.get_self_calling(simple)
            original_test_case_id = self.config.database.insert_original_testcase(testcase=original_test_case,
                                                                                  simple=simple)

            self.config.database.update_simple_status(simple)  # 将这个函数标记过已经被使用过了，不会重复测试
            mutated_test_case_list = self.config.mutator.mutate(original_test_case, max_size=20)
            mutated_test_case_list.append(original_test_case)
            while len(mutated_test_case_list) > 0:
                mutated_test_case = mutated_test_case_list.pop(0)
                harness_result = self.config.harness.run_testcase(mutated_test_case)
                # 更新engine.outputs中的每一元素的id为数据库中的id,若数据已经存储过，则返回None
                [harness_result, test_case_id] = self.config.database.insert_harness_result(harness_result,
                                                                                            original_test_case_id)
                differential_test_result = Result.differential_test(harness_result)
                if len(differential_test_result) == 0:
                    continue
                self.config.database.insert_differential_test_results(differential_test_result)
                need_simplify = False
                for info in differential_test_result:
                    [classify_result, classify_id] = self.config.classifier.is_suspicious_result(info.output_id,
                                                                                                 harness_result)
                    info.classify_result = classify_result.value
                    info.classify_id = classify_id
                    # 存储过滤的结果，用于判断测试结果过滤是否出错
                    self.save_filtered_result(differential_test_result, harness_result)
                    need_simplify |= classify_result.value > 0  # 判断是否存在未被过滤的测试结果
                self.config.database.insert_differential_test_results(differential_test_result)

                # 为了节约时间，性能缺陷先不进行测试用例精简
                for per in differential_test_result:
                    if per.bug_type == "Performance issue":
                        need_simplify = False
                        break

                if need_simplify:
                    simplify_start_time = labdate.GetUtcMillisecondsNow()
                    simplified_test_case = self.config.reducer.reduce(harness_result)
                    simplify_end_time = labdate.GetUtcMillisecondsNow()
                    # 用例精简过程中变异出的能测试出新“bug”的测试用例
                    delete_mutation_test_case_list = [e.testcase for e in self.config.reducer.mutated_harness_result_list]
                    mutated_test_case_list.extend(delete_mutation_test_case_list)
                    simple_duration_ms = labdate.Datetime2Ms(simplify_end_time - simplify_start_time)
                    self.config.database.insert_auto_simplified_testcase(test_case_id, simplified_test_case,
                                                                         simple_duration_ms)
                    # 将可疑测试结果存储为文件，便于分析。需存储最原始的测试用例，变异后的测试用例，原始的测试结果
                    self.save_suspicious_result(simplified_test_case, differential_test_result, mutated_test_case,
                                                original_test_case, harness_result)
            self.config.database.update_simple_status(simple)  # 将这个函数标记过已经被使用过了，不会重复测试
        self.config.classifier.print_statistical_results()

    def save_suspicious_result(self, simplified_test_case, differential_test_result, mutated_test_case,
                               original_test_case, harness_result):
        simplified_code_md5 = crypto.md5_str(simplified_test_case)  # 精简后测试用例相同的测试结果放在同一目录下
        file_name = str(int(time.time())) + ".txt"  # 以发现bug得时间戳（秒）为文件存储测试结果
        file_path = self.config.workspace / f"result-files/{simplified_code_md5}/{file_name}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = ""
        content += "==================simplified test case===========================\n\n"
        content += simplified_test_case
        content += f"\n\n==================differential test result: {len(differential_test_result)}" \
                   f"=================\n\n "
        content += json.dumps([e.serialize() for e in differential_test_result], indent=4)
        content += "\n\n==================mutated test case==============================\n\n"
        content += mutated_test_case
        content += "\n\n==================original test case=============================\n\n"
        content += original_test_case
        content += "\n\n==================harness result=================================\n\n"
        content += str(harness_result)
        file_path.write_text(content)
        # print(content)

    def save_filtered_result(self, differential_test_result, harness_result: Result.HarnessResult):
        """
        存储被判定为重复的测试结果
        """
        file_name = str(int(time.time())) + ".txt"  # 以发现bug得时间戳（秒）为文件存储测试结果
        classify_ids_set = set([info.classify_id for info in differential_test_result])
        for classify_id in classify_ids_set:
            file_path = self.config.workspace / f"filtered-result/classify_id_{classify_id}/{file_name}"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = ""
            content += "\n\n==================mutated test case==============================\n\n"
            content += harness_result.testcase
            content += f"\n\n==================differential test result: {len(differential_test_result)}" \
                       f"=================\n\n "
            content += json.dumps([e.serialize() for e in differential_test_result], indent=4)
            content += "\n\n==================harness result=================================\n\n"
            content += str(harness_result)
            file_path.write_text(content)


if __name__ == '__main__':
    try:
        Fuzzer().main()
    except RuntimeError:
        sys.exit(1)
