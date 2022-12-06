# coding:utf-8
import pathlib
import sqlite3

from Result import *


class DBOperation:
    def __init__(self, db_path: str):  # pathlib不支持参数传递，参数传递后类型发生改变
        # 用于测试，记得删除
        # pathlib.Path(db_path).unlink()

        self.conn = sqlite3.connect(db_path)
        self.create_tables()

        # 用于测试，记得删除
        # self.init_simples()

    def close(self):
        """
        关闭所有数据库资源
        """
        self.conn.close()

    def create_tables(self):
        """
        创建数据库表
        """
        cursor = self.conn.cursor()
        # sql_file_path = pathlib.Path("./src/db/tables.sql").absolute().resolve()
        sql_file_path = pathlib.Path("/home/yhy/EmbeddedFuzzer/src/db/tables.sql").absolute().resolve()
        sql_list = [e for e in sql_file_path.read_text().replace("\n", "").split(";") if e != '']
        try:
            for sql in sql_list:
                cursor.execute(sql)
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e

    def query_corpus(self, unused_only=True) -> List[str]:
        """
        查询所有函数，并以列表的形式返回
        :param unused_only: 是否只查询未被已经被使用过的函数，True表示只查询未被使用过的函数，否则查询所有的函数
        :return:
        """
        sql = "select simple from Corpus"
        if unused_only:
            sql = "select simple from Corpus WHERE used=0"
        testcases = [e[0] for e in self.query_template(sql)]
        return testcases

    def query_template(self, sql: str, values: list = None) -> list:
        """
        执行查询语句并返回执行结果, 返回值是一个二维表
        """
        cursor = self.conn.cursor()
        try:
            if values is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, values)
            result = cursor.fetchall()
        except BaseException as e:
            raise e
        finally:
            cursor.close()
        return result

    def insert_original_testcase(self, testcase: str, simple: str) -> int:
        """
        插入original_testcase并返回original_testcase在数据库中的id
        当testcase重复时，返回其id
        :param simple:
        :param testcase:
        :return:
        """
        sql = "select id from Corpus where simple=?"
        simple_id = self.query_template(sql, [simple])[0][0]
        sql_insert = "insert or ignore into OriginalTestcases(testcase, simple_id) values(?,?)"
        original_testcase_id = self.insert_template(sql_insert, [testcase, simple_id])
        if original_testcase_id is None:  # 测试用例已经被存储过了
            query_id_sql = "select id from OriginalTestcases where testcase=?"
            original_testcase_id = self.query_template(query_id_sql, [testcase])[0][0]
        return original_testcase_id

    def insert_harness_result(self, harness_result: HarnessResult, original_testcase_id: int) -> list:
        """
        存储测试测试结果中的测试用例和output，并设置output的id, 并返回测试用例的id
        :param harness_result:
        :param original_testcase_id:
        :return:
        """
        cursor = self.conn.cursor()
        insert_testcase_sql = f"INSERT OR IGNORE INTO Testcases (original_testcase_id,testcase) VALUES(?,?)"
        insert_engines_sql = f"INSERT OR IGNORE INTO Engines (testbed) VALUES(?)"
        insert_harness_result_sql = f"INSERT OR ignore INTO Outputs(" \
                                    f"testcase_id,testbed_id,returncode,stdout,stderr," \
                                    f"duration_ms,event_start_epoch_ms) " \
                                    f"VALUES(?,?,?,?,?,?,?)"
        max_str_len = int((2 ** 31-1) / 2)  # 删减存储的字符串，出现错误OverflowError: string longer than INT_MAX bytes
        try:
            cursor.execute(insert_testcase_sql, [original_testcase_id, harness_result.testcase])
            # 测试用例重复出现，放弃此测试结果
            if cursor.rowcount == 0:
                return [None, None]
            testcase_id = cursor.lastrowid
            for output in harness_result.outputs:
                read_result = self.query_template("SELECT id FROM Engines WHERE testbed=?", [output.testbed])
                if len(read_result) == 0:  # 引擎没有存储过
                    cursor.execute(insert_engines_sql, [output.testbed])
                    testbed_id = cursor.lastrowid
                else:
                    testbed_id = read_result[0][0]
                cursor.execute(insert_harness_result_sql, [
                    testcase_id, testbed_id, output.returncode, str(output.stdout)[:max_str_len],
                    str(output.stderr)[:max_str_len], output.duration_ms, output.event_start_epoch_ms])
                # cursor.execute(insert_harness_result_sql, [
                #     testcase_id, testbed_id, output.returncode, output.stdout,
                #     output.stderr, output.duration_ms, output.event_start_epoch_ms])
                output.id = cursor.lastrowid
            self.conn.commit()
            # 保证事务的原子性
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
        return [harness_result, testcase_id]

    def insert_differential_test_results(self, bugs_info_list: List[DifferentialTestResult]):
        """
        将差分测试后并进行过滤后的测试结果存储到输库
        :param bugs_info_list:
        :return:
        """
        cursor = self.conn.cursor()
        insert_diff_test_result_sql = f"INSERT OR IGNORE INTO DifferentialTestResults (" \
                                      f"bug_type,output_id,classify_result,classify_id) " \
                                      f"VALUES(?,?,?,?)"
        try:
            for bug_info in bugs_info_list:
                cursor.execute(insert_diff_test_result_sql, [bug_info.bug_type, bug_info.output_id,
                                                             bug_info.classify_result, bug_info.classify_id])
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def insert_corpus(self, simple: str) -> int:
        """
        将simple保存到数据库，并返回其在Corpus表中的主键id
        :param simple:
        :return:
        """
        sql = f"INSERT OR IGNORE INTO Corpus (simple) VALUES(?)"
        return self.insert_template(sql, [simple])

    def insert_template(self, sql: str, values: list) -> int:
        """
        存储数据并返回其主键索引
        :param sql: 
        :param values: 
        :return: 
        """
        cursor = self.conn.cursor()
        identify = None
        try:
            cursor.execute(sql, values)
            # 数据在数据库表中唯一且存储成功，返回唯一标识此测试用例的id
            if cursor.rowcount != 0:
                identify = cursor.lastrowid
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
        return identify

    # def init_simples(self):
    #     path = pathlib.Path("./test/data/testcase")
    #     for p in path.rglob("*.js"):
    #         case = p.read_text()
    #         simple_id = self.insert_corpus(case)
    #         print(simple_id)

    def insert_auto_simplified_testcase(self, testcase_id: int, auto_simplified_testcase: str, simplified_duration_ms):
        cursor = self.conn.cursor()
        sql = f"UPDATE Testcases set auto_simplified_testcase=?, auto_simplified_duration_ms=? where id=?;"
        try:
            cursor.execute(sql, [auto_simplified_testcase, simplified_duration_ms, testcase_id])
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def update_simple_status(self, simple: str):
        cursor = self.conn.cursor()
        sql = "update Corpus set used=1 WHERE simple=?"
        try:
            cursor.execute(sql, [simple])
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def query_mutated_test_case(self, test_case_id: int = -1, limit: int = -1):
        if test_case_id != -1:
            sql = "SELECT id, testcase FROM Testcases WHERE id=?;"
            return self.query_template(sql, [test_case_id])
        else:
            if limit > 0:
                sql = "SELECT id, testcase FROM Testcases WHERE auto_simplified_testcase NOT NULL AND is_manual_check = 0 LIMIT ?;"
                return self.query_template(sql, [limit])
            else:
                sql = "SELECT id, testcase FROM Testcases WHERE auto_simplified_testcase NOT NULL AND is_manual_check = 0;"
                return self.query_template(sql)

    def query_mutated_test_case_randomly(self):
        # 随机获取一个触发缺陷的测试用例
        sql = "SELECT id, testcase FROM Testcases WHERE auto_simplified_testcase NOT NULL AND is_manual_check = 0 " \
              "order by RANDOM() limit 1;"
        # 随机获取一个性能缺陷的测试用例
        sql = """SELECT id, testcase FROM Testcases WHERE auto_simplified_testcase NOT NULL AND is_manual_check = 0 AND Testcases.id in (select distinct(O.testcase_id) from Outputs O INNER JOIN DifferentialTestResults D WHERE O.id=D.output_id AND D.bug_type="Performance issue") order by RANDOM() limit 1;"""
        # 顺序获取一个性能缺陷的测试用例
        sql = """SELECT id, testcase FROM Testcases WHERE is_manual_check = 0 AND Testcases.id in (select distinct(O.testcase_id) from Outputs O INNER JOIN DifferentialTestResults D WHERE O.id=D.output_id AND D.bug_type="Performance issue") limit 1;"""
        return self.query_template(sql)

    def update_test_case_manual_checked_state(self, test_case_id: int):
        cursor = self.conn.cursor()
        sql = "update Testcases set is_manual_check=1 WHERE id=?"
        try:
            cursor.execute(sql, [test_case_id])
            self.conn.commit()
        except BaseException as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    # def query_corpus(self, table_name: str, feild: str,):
    #     conn = sqlite3.connect(self.db_path)
    #     cursor = conn.cursor()
    #     sql = f"SELECT {feild} FROM {table_name}"
    #     cursor.execute(sql)
    #     result = cursor.fetchall()
    #     conn.close()
    #     return result
    #
    # def insert_original_testcase(self, testcase: str) -> int:
    #     """
    #     将变异前的测试用例存储到数据库中
    #     :param testcase: 需要存储的原始测试用例
    #     :return: 若测试用例插入成功，则返回数据库表中的id；若数据库表中已经存在相同的测试用例，则返回None
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     cursor = conn.cursor()
    #     insert_original_testcase_sql = f"INSERT OR IGNORE INTO OriginalTestcases (testcase) VALUES(?)"
    #     testcase_id = None
    #     try:
    #         cursor.execute(insert_original_testcase_sql, [testcase])
    #         # 测试用例在数据库表中唯一且存储成功，返回唯一标识此测试用例的id
    #         if cursor.rowcount != 0:
    #             testcase_id = cursor.lastrowid
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #         return testcase_id
    #
    # def insert_harness_result(self, result: HarnessResult, original_testcase_id):
    #     """
    #     将测试结果插入数据库
    #     :param result: 差分测试后测试结果
    #     :param original_testcase_id:这个测试用例是从哪个测试用例变异而来的
    #     :return:
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     cursor = conn.cursor()
    #     insert_testcase_sql = f"INSERT OR IGNORE INTO Testcases (original_testcase,testcase) VALUES(?,?)"
    #     insert_engines_sql = f"INSERT OR ignore INTO Engines (testbed) VALUES(?)"
    #     insert_harness_result_sql = f"INSERT OR ignore INTO HarnessResults " \
    #         f"(testcase,testbed,returncode,stdout,stderr,duration_ms,event_start_epoch_ms) " \
    #         f"VALUES(?,?,?,?,?,?,?)"
    #     testcase_id = None
    #     try:
    #         cursor.execute(insert_testcase_sql, [original_testcase_id, result.testcase])
    #         # 测试用例重复出现，放弃此测试结果
    #         if cursor.rowcount == 0:
    #             return [None, testcase_id]
    #         testcase_id = cursor.lastrowid
    #         for output in result.outputs:
    #             read_result = self.query_with_params("SELECT id FROM Engines WHERE testbed=?", [output.testbed])
    #             if len(read_result) == 0:
    #                 cursor.execute(insert_engines_sql, [output.testbed])
    #                 testbed_id = cursor.lastrowid
    #             else:
    #                 testbed_id = read_result[0][0]
    #             cursor.execute(insert_harness_result_sql, (
    #                 testcase_id, testbed_id, output.returncode, output.stdout,
    #                 output.stderr, output.duration_ms, output.event_start_epoch_ms))
    #             output.id = cursor.lastrowid
    #         conn.commit()
    #         # 保证事务的原子性
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #     return [result, testcase_id]
    #
    # def insert_differential_test_results(self, bug_info_list: list):
    #     conn = sqlite3.connect(self.db_path)
    #     insert_diff_test_result_sql = f"INSERT OR IGNORE INTO DifferentialTestResults (bugType,output_id) VALUES(?,?)"
    #     try:
    #         cursor = conn.cursor()
    #         for bug_info in bug_info_list:
    #             cursor.execute(insert_diff_test_result_sql, bug_info)
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def insert_suspicious_results(self, bug_info_list: list):
    #     # 将可以的测试用例存储起来，方便进行手动分析
    #     conn = sqlite3.connect(self.db_path)
    #     insert_diff_test_result_sql = f"INSERT OR IGNORE INTO SuspiciousResults (bugType,output_id,classifyId) VALUES(?,?,?)"
    #     try:
    #         cursor = conn.cursor()
    #         for bug_info in bug_info_list:
    #             cursor.execute(insert_diff_test_result_sql, bug_info)
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def insert_filtered_results(self, bug_info_list: list):
    #     # 存储被过滤了，不需要再进行手动分析的测试结果
    #     conn = sqlite3.connect(self.db_path)
    #     insert_diff_test_result_sql = f"INSERT OR IGNORE INTO FilteredResults (bugType,output_id,classifyId) VALUES(?,?,?)"
    #     try:
    #         cursor = conn.cursor()
    #         for bug_info in bug_info_list:
    #             cursor.execute(insert_diff_test_result_sql, bug_info)
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def insert_no_exception_results(self, bug_info_list: list):
    #     # 存储过滤后被保留、需要手动分析的、所有引擎都没有抛异常的测试结果
    #     conn = sqlite3.connect(self.db_path)
    #     insert_diff_test_result_sql = f"INSERT OR IGNORE INTO FilteredNoExceptionResults (bugType,output_id,classifyId) VALUES(?,?,?)"
    #     try:
    #         cursor = conn.cursor()
    #         for bug_info in bug_info_list:
    #             cursor.execute(insert_diff_test_result_sql, bug_info)
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def insert_original_testcase_duration_ms(self, oringinal_testcase_id: int, duration_ms, simplify_duration_ms):
    #     conn = sqlite3.connect(self.db_path)
    #     insert_original_testcase_duration_ms_sql = f"INSERT OR IGNORE INTO OriginalTestcaseExecutionTime (testcase_id, duration_ms, simplify_duration_ms) VALUES(?,?,?)"
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(insert_original_testcase_duration_ms_sql,
    #                        [oringinal_testcase_id, duration_ms, simplify_duration_ms])
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def insert_auto_simplified_testcase(self, auto_simplified_testcase: int, testcase_id):
    #     conn = sqlite3.connect(self.db_path)
    #     sql = f"UPDATE Testcases set auto_simplified_testcase=? where id=?;"
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(sql, [auto_simplified_testcase, testcase_id])
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def query_harness_result_with_testcase_id(self, testcase_id: int):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT testcase FROM Testcases WHERE id=?", [testcase_id])
    #         testcase = cursor.fetchall()[0][0]
    #         result = HarnessResult(testcase)
    #         query_outputs_sql = "SELECT h.id, Testcases.testcase, Engines.testbed, h.returncode, h.stdout, h.stderr, h.duration_ms, h.event_start_epoch_ms From HarnessResults h INNER JOIN Testcases INNER JOIN Engines on h.testcase=Testcases.id AND h.testbed=Engines.id AND h.testcase=?"
    #         cursor.execute(query_outputs_sql, [testcase_id])
    #         for output in cursor.fetchall():
    #             out = Output(output[0], output[2], output[3], output[4], output[5], output[6], output[7])
    #             result.outputs.append(out)
    #     finally:
    #         conn.close()
    #     return result
    #
    # def query_harness_result_with_harness_result_id(self, suspicious_result_id: int):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT testcase FROM HarnessResults WHERE id=?", [suspicious_result_id])
    #         testcase_id = cursor.fetchall()[0][0]
    #     finally:
    #         conn.close()
    #     result = self.query_harness_result_with_testcase_id(testcase_id)
    #     return result
    #
    # def query_all_suspicious_result_ids(self):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = "SELECT output_id FROM SuspiciousResults"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return [e[0] for e in result]
    #
    # def query_all_differential_test_result(self):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = "SELECT bugType, output_id FROM DifferentialTestResults"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return result
    #
    # def query_all_testbeds(self):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = f"SELECT testbed FROM Engines"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return [e[0] for e in result]
    #
    # def query_all_testcases(self):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = f"SELECT testcase FROM Testcases"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return [e[0] for e in result]
    #
    # def query_testcase_with_id(self, testcase_id: int):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = f"SELECT testcase FROM Testcases WHERE id=?"
    #         cursor.execute(sql, [testcase_id])
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return result[0][0]
    #
    # def query_all_testcases_ids(self):
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         sql = f"SELECT id FROM Testcases"
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return [e[0] for e in result]
    #
    # def query_with_params(self, sql: str, params: list):
    #     """
    #     EXecute query statement and return the query result.
    #     :arg
    #         sql: the query statement want to execute.
    #     :return
    #         the query result
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(sql, params)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return result
    #
    # def execute_with_params(self, sql: str, params: list):
    #     """
    #     EXecute query statement and return the query result.
    #     :arg
    #         sql: the query statement want to execute.
    #     :return
    #         the query result
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(sql, params)
    #         conn.commit()
    #     except Exception as e:
    #         logging.warning(e.args[0])
    #         conn.rollback()
    #     finally:
    #         conn.close()
    #
    # def query(self, sql: str):
    #     """
    #     EXecute query statement and return the query result.
    #     :arg
    #         sql: the query statement want to execute.
    #     :return
    #         the query result
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #     finally:
    #         conn.close()
    #     return result
    #
    # def execute(self, sql: str):
    #     """
    #     Execute the statement of sql to modify the database, and commint the operation to database.
    #
    #     :arg
    #     sql: the sql statement want to execute.
    #     """
    #     conn = sqlite3.connect(self.db_path)
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute(sql)
    #         conn.commit()
    #     except Exception:
    #         conn.rollback()
    #     finally:
    #         conn.close()
