import json
import pathlib

from db.db_operation import DBOperation


def get_index(config=pathlib.Path("./config.pbtxt")) -> list:
    if not config.exists():
        raise Exception(f"File not exist: {str(config)}")

    return [int(i) for i in list(filter(str.isdigit, config.read_text().split("\n")))]


if __name__ == '__main__':
    db_path = r"F:\documents\GitHub\javascriptFuzzingData\qx_1st\result-2020-05-20.db"
    suspicious_result_ids_path = "./data/suspicious_result_ids.txt"
    suspicious_result_ids = get_index(pathlib.Path(suspicious_result_ids_path))
    db = DBOperation(pathlib.Path(db_path))
    # 初次读取测试结果，则从数据库中进行读取
    if len(suspicious_result_ids) == 0:
        suspicious_result_ids = db.query_all_suspicious_result_ids()
    while len(suspicious_result_ids) > 0:
        result = db.query_harness_result_with_harness_result_id(suspicious_result_ids[0])
        same_testcase_ids = list_intersection(get_identifiers(result), suspicious_result_ids)
        suspicious_result_ids = remove_from(same_testcase_ids, suspicious_result_ids)
        # serialized_result = json.udmps(result.serialize(), indent=2)  # indent=2 美化json
        print(result)
        print("********************************************************************************")
        print("{0:*^80}".format(str(same_testcase_ids)))
        print("********************************************************************************")
        with open("./data/result.json", "w") as f:
            f.write(serialized_result)
        pathlib.Path("./data/testcase.js").write_text(result.testcase)
        breakpoint()
        pathlib.Path(suspicious_result_ids_path).write_text("\n".join([str(e) for e in suspicious_result_ids]))
