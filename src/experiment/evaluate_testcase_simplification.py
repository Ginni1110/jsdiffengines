# coding=utf-8
import json
import logging
import pathlib
import subprocess
import sys
import tempfile
from tqdm import tqdm

from Reducer.reduce_with_lithium import simplify_with_lithium
from Configer import Config
from utils import JSASTOpt
from utils import labdate

sys.path.extend(['/home/yhy/EmbeddedFuzzer', '/home/yhy/EmbeddedFuzzer/resources', '/home/yhy/EmbeddedFuzzer/src'])
logging.basicConfig(level=logging.WARN,
                    format='%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Fuzzer:
    def __init__(self):
        config_path = "./resources/config.json"
        self.config = Config(config_path)
        # self.config.init_data()

    def main(self):
        try:
            self.run()
        except BaseException as e:
            raise e
        finally:
            self.config.close_resources()

    def run(self):
        self.lithium()
        self.lithium_algorithm()
        self.ast_based_lithium_algorithm()

        # self.ast_based()
        # self.lithium_evaluate("./test/data/lithium_simplified_testcase.json")
        # self.lithium_evaluate("./test/data/lithium_algorithm_simplified_testcase.json")
        # self.lithium_algorithm()

        # self.evaluate_with_tokens("./test/data/ast_based_lithium_algorithm_optimization_declaration.json")
        # self.evaluate_with_tokens("./test/data/lithium_algorithm_simplified_testcase.json")
        # self.evaluate_with_tokens("./test/data/lithium_simplified_testcase.json")

    def lithium(self):
        """
        lithium的精简算法和lithium的基于输出信息的精简判断条件
        :return:
        """
        testcase_list = json.loads(pathlib.Path("./test/data/testcase.json").read_text())
        simplified_reuslt_path = pathlib.Path("./test/data/lithium_simplified_testcase.json")
        original2simplified = []
        for testcase in tqdm(testcase_list):
            print("\n")
            harness_result = self.config.harness.run_testcase(testcase)
            simplify_start_time = labdate.GetUtcMillisecondsNow()
            simplified_testcase = simplify_with_lithium(harness_result)
            simplify_end_time = labdate.GetUtcMillisecondsNow()
            simplify_duration_ms = labdate.Datetime2Ms(simplify_end_time - simplify_start_time)
            original2simplified.append(
                {"original": testcase, "simplified": simplified_testcase, "duration": simplify_duration_ms})
            simplified_reuslt_path.write_text(json.dumps(original2simplified, indent=4))

    def lithium_algorithm(self):
        """
        使用lithium的算法和我们的基于多为信息的精简判断条件
        :return:
        """
        testcase_list = json.loads(pathlib.Path("./test/data/testcase.json").read_text())
        simplified_reuslt_path = pathlib.Path("./test/data/lithium_algorithm_simplified_testcase.json")
        original2simplified = []
        for testcase in tqdm(testcase_list):
            print("\n")
            with tempfile.NamedTemporaryFile(prefix="javascriptTestcase_", suffix=".js", delete=True) as f:
                testcase_path = pathlib.Path(f.name)
                testcase_path.write_text(testcase)
                simplify_start_time = labdate.GetUtcMillisecondsNow()
                self.simplify_with_lithium_algorithm_our_interesting(testcase_path)
                simplify_end_time = labdate.GetUtcMillisecondsNow()
                simplify_duration_ms = labdate.Datetime2Ms(simplify_end_time - simplify_start_time)
                simplified_testcase = testcase_path.read_text()
                original2simplified.append(
                    {"original": testcase, "simplified": simplified_testcase, "duration": simplify_duration_ms})
                simplified_reuslt_path.write_text(json.dumps(original2simplified, indent=4))

    def ast_based_lithium_algorithm(self):
        """
        基于AST树进行精简，同一层节点使用ddmin算法进行精简
        :return:
        """
        testcase_list = json.loads(pathlib.Path("./test/data/testcase.json").read_text())
        simplified_reuslt_path = pathlib.Path("./test/data/ast_based_lithium_algorithm_optimization_declaration.json")
        original2simplified = []
        for testcase in tqdm(testcase_list):
            harness_result = self.config.harness.run_testcase(testcase)
            simplify_start_time = labdate.GetUtcMillisecondsNow()
            simplified_testcase = self.config.reducer.reduce(harness_result)
            simplify_end_time = labdate.GetUtcMillisecondsNow()
            simplify_duration_ms = labdate.Datetime2Ms(simplify_end_time - simplify_start_time)
            original2simplified.append(
                {"original": testcase, "simplified": simplified_testcase, "duration": simplify_duration_ms})
            simplified_reuslt_path.write_text(json.dumps(original2simplified, indent=4))

    def evaluate_with_tokens(self, file_path):
        """
        评估测试用例精简的力度。计算测试用例精简前后的token数量。
        :param file_path:
        :return:
        """
        simplified_reuslt_path = pathlib.Path(file_path).absolute().resolve()
        simplified_reuslt = json.loads(simplified_reuslt_path.read_text())
        total_duration = 0
        total_original_token = 0
        total_simplified_token = 0
        testcase_size = 0
        for ele in simplified_reuslt:
            try:
                testcase_size += 1
                total_original_token += len(JSASTOpt.tokenize(ele["original"]))
                total_simplified_token += len(JSASTOpt.tokenize(ele["simplified"]))
                total_duration += ele["duration"]
            except BaseException as e:
                pass
        print(f"\n{'=' * 20}{simplified_reuslt_path}{'=' * 20}")
        print(simplified_reuslt_path.absolute().resolve())
        print(f"Test case Counter: {testcase_size}")
        print(f"Averaged Simplify Duration: {total_duration / testcase_size} ms")
        print(f"Original Averaged  Tokens: {total_original_token / testcase_size} ")
        print(f"Remained Averaged Tokens: {total_simplified_token / testcase_size} ")
        print(f"Deleted Averaged Tokens: {(total_original_token - total_simplified_token) / total_original_token}")

    def simplify_with_lithium_algorithm_our_interesting(self, testcase_path: pathlib.Path):
        """
        使用lithium基于代码行的测试用例精简方法进行精简，判断条件使用本文基于多维特征的精简判断条件对测试用例进行精简
        :param testcase_path:
        :return:
        """
        pro = subprocess.Popen(["/home/yhy/EmbeddedFuzzer/src/experiment/test.sh", str(testcase_path)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = pro.communicate()
        if stderr != "":
            print(stderr)

    def ast_based_individually(self):
        """
        对每一层节点进行删除时，逆序逐行删除
        :return:
        """
        testcase_dict = json.loads(pathlib.Path("./test/data/original_testcase.json").read_text())
        total_duration = 0
        total_original_line = 0
        total_simplified_line = 0
        testcase_size = 0
        testcase_list = []
        for element in tqdm(dict(testcase_dict).values()):
            if element["auto_simplified_testcase"] is not None and len(
                    str(element["auto_simplified_testcase"]).strip().split("\n")) > 2:
                original_testcase = str(element["testcase"])
                testcase_size += 1
                testcase_list.append(original_testcase.strip())
                total_duration += element["auto_simplified_duration_ms"]
                total_original_line += len(original_testcase.strip().split("\n"))
                total_simplified_line += len(str(element["auto_simplified_testcase"]).strip().split("\n"))
        pathlib.Path("./test/data/testcase.json").write_text(json.dumps(testcase_list))
        print(f"\n{'=' * 20}基于抽象语法树的测试用例精简方法{'=' * 20}")
        print(f"Test case Counter: {testcase_size}")
        print(f"Averaged Simplify Duration: {total_duration / testcase_size} ms")
        print(f"Original Averaged  Lines: {total_original_line / testcase_size} ")
        print(f"Remained Averaged Lines: {total_simplified_line / testcase_size} ")
        print(f"Deleted Averaged Lines: {(total_original_line - total_simplified_line) / total_original_line}")

    def get_test_case(self):
        sql = """
        SELECT T.id, T.testcase, T.auto_simplified_testcase, T.auto_simplified_duration_ms,T.original_testcase_id FROM Testcases T WHERE id in (SELECT DISTINCT(O.testcase_id) FROM Outputs O WHERE O.id in (SELECT DTR.output_id from DifferentialTestResults DTR WHERE DTR.bug_type != "Performance issue") LIMIT 1000000);
        """
        # 现有的方法无法精简触发性能缺陷的测试用例，评估测试用例精简方法时剔除了触发性能缺陷的测试用例。
        query_result = self.config.database.query_template(sql)
        print(len(query_result))
        serializable_result = {e[4]: {"id": e[0], "testcase": e[1], "auto_simplified_testcase": e[2], "auto_simplified_duration_ms" : e[3], "original_testcase_id": e[4]} for e in query_result}
        txt = json.dumps(serializable_result)
        print(len(serializable_result.keys()))
        pathlib.Path("./test/data/original_testcase.json").write_text(txt)

    def evaluate_with_lines(self, file_path):
        """
        评估测试用例精简的力度。计算测试用例精简前后的行数。
        :param file_path:
        :return:
        """
        simplified_reuslt_path = pathlib.Path(file_path).absolute().resolve()
        simplified_reuslt = json.loads(simplified_reuslt_path.read_text())
        total_duration = 0
        total_original_line = 0
        total_simplified_line = 0
        testcase_size = len(simplified_reuslt)
        for ele in simplified_reuslt:
            total_original_line += len(ele["original"].strip().split("\n"))
            total_simplified_line += len(ele["simplified"].strip().split("\n"))
            total_duration += ele["duration"]
        print(f"\n{'=' * 20}{simplified_reuslt_path}{'=' * 20}")
        print(simplified_reuslt_path.absolute().resolve())
        print(f"Test case Counter: {testcase_size}")
        print(f"Averaged Simplify Duration: {total_duration / testcase_size} ms")
        print(f"Original Averaged  Lines: {total_original_line / testcase_size} ")
        print(f"Remained Averaged Lines: {total_simplified_line / testcase_size} ")
        print(f"Deleted Averaged Lines: {(total_original_line - total_simplified_line) / total_original_line}")


if __name__ == '__main__':
    try:
        Fuzzer().main()
    except RuntimeError:
        sys.exit(1)
