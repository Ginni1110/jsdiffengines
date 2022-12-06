import json

from Reducer.Reduce import Reducer
from utils import getApisFromTestcase
from ResultFilter.classify import Classifier
from db import db_operation
from Harness import *
from Postprocessor.callable_processor import CallableProcessor
from utils.parseTestbed import TestbedParser
from ResultFilter.errorinfo_classifier.errorinfo_db_operation import DataBase
from Mutator.mutation import Mutator
from utils.uniformVariableName import Uniform


class Config:
    def __init__(self, config_path: str):
        self.config_path = str(pathlib.Path(config_path).absolute().resolve())
        self.config_check()
        with open(config_path, "r") as f:
            config = json.load(f)
        self.config = config
        self.workspace = pathlib.Path(config["workspace"])
        db_path = pathlib.Path(config["db_path"])
        self.error_info = self.workspace / "exception-info"
        self.api_instance = getApisFromTestcase.ESAPI(config["ESApis"])
        self.database = db_operation.DBOperation(str(db_path))
        self.harness = Harness(config["testbeds"], config["harness"]["mode"], config["harness"]["processes_num"])
        self.testbed_parser = TestbedParser(config["testbeds"])
        self.classify_db = DataBase(config["classify_db"])
        self.classifier = Classifier(self.api_instance, self.testbed_parser, self.classify_db)
        self.mutator = Mutator("node")
        self.reducer = Reducer()
        self.uniform = Uniform()

        self.error_info.mkdir(parents=True, exist_ok=True)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.simples = None
        self.callable_processor = None
        # self.init_data()

    def init_data(self):
        logging.info("Loading simples...")
        self.simples = self.database.query_corpus()
        # 待优化：这里一次行读出了所有的simple可能会导致内存崩溃
        self.callable_processor = CallableProcessor(self.simples)

    def config_check(self):
        if not pathlib.Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not exist: {self.config_path}")
        with open(self.config_path, "r") as f:
            config = json.load(f)
        simple_db = pathlib.Path(config["db_path"]).absolute().resolve()
        if not simple_db.is_file() or not simple_db.exists():
            # 可以进一步检查
            raise FileNotFoundError(f"Corpus db file not exist: {simple_db}")
        # 检查分类数据库是否可以正常使用，
        classify_db = pathlib.Path(config["classify_db"])
        # 链接数据库，检查数据库是否可以正常使用

        # 检查待测试的JS引擎是否可以正常测试
        engines = config["testbeds"]
        self.engines_check(engines)

    def engines_check(self, testbeds: List[str]) -> bool:
        """
        check all engines is available
        :return:
            if all engines is available return ture, otherwise raise exception.
        :raise
            raise exception if any engine is not available.
        """
        if len(testbeds) == 0:
            raise Exception("No engine available, please check the configuration file.")
        with tempfile.NamedTemporaryFile(prefix="JavaScriptTestcase_", suffix=".js", delete=True) as f:
            p = pathlib.Path(f.name)
            p.write_text("var a = 1;\nprint(a);")

            for bed in testbeds:
                result = run_test_case(bed, p)
                if not result.returncode == 0:
                    logging.error(f"Enigine ERROR: {bed}\n"
                                  f"returncode = {str(result.returncode)}")
                    raise LookupError(f"Enigine ERROR: {bed}\n")
                # # 再增加其他的检查方式，比如直接执行jerry命令等方式，确保每一个引擎都是可以运行的
                elif result.stdout != "1\n":
                    raise Exception(f"Engine cannot be tested:\n {bed}. \n"
                                    f"When run the test case bellow, whose output should be \"1\\n\", but it's output is: \n"
                                    f"{result.stdout}")

    def close_resources(self):  # 关闭所有配置文件资源
        self.database.close()
