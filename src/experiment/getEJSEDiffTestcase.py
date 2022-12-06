import logging
import sys
import pathlib

from Configer import Config

sys.path.extend(['/home/yhy/EmbeddedFuzzer', '/home/yhy/EmbeddedFuzzer/src'])
logging.basicConfig(level=logging.INFO,
                    format='%(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Comparision:
    def __init__(self):
        config_path = "./resources/config.json"
        self.config = Config(config_path)

    def main(self):
        try:
            self.run()
        except BaseException as e:
            raise e
        finally:
            self.config.close_resources()

    def run(self):
        # 顺序命名
        # sql = "select testcase from OriginalTestcases limit 20000" # 顺序获取
        # sql = "select id, testcase from OriginalTestcases order by RANDOM() limit 20000" # 随机获取
        # testcase_list = [e[0] for e in self.config.database.query_template(sql=sql)]
        # testcase_dir = pathlib.Path("/home/yhy/codeCoverage/EJSEDiff/EJSEDiff_corpus_random")
        # testcase_dir.mkdir(parents=True, exist_ok=True)
        # for i in range(len(testcase_list)):
        #     # print(testcase_dir / f"{i + 1}.js")
        #     (testcase_dir / f"{i + 1}.js").write_text(testcase_list[i])

        # 以testcase的id作为文件名
        sql = "select id, testcase from OriginalTestcases order by RANDOM() limit 20000"
        testcase_list = self.config.database.query_template(sql=sql)
        testcase_dir = pathlib.Path("/home/yhy/codeCoverage/EJSEDiff/EJSEDiff_corpus_random_testcase_id")
        testcase_dir.mkdir(parents=True, exist_ok=True)
        for id, testcase in testcase_list:
            (testcase_dir / f"{id}.js").write_text(testcase)
        print(len(testcase_list))


if __name__ == '__main__':
    try:
        Comparision().main()
    except RuntimeError:
        sys.exit(1)