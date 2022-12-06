import pathlib
import re
from pandas import DataFrame


def getJavaScriptAPI(inputFile: pathlib.Path, outputFile: pathlib.Path):
    with open(str(inputFile), "r", encoding="utf-8") as f:
        inputText = f.read()
    pattern = re.compile("(<td rowspan=\"2\"><a href=\".*\">)(.*)(</a></td>)")
    result = [item[1] for item in pattern.findall(inputText)]
    DataFrame(result).to_excel(outputFile, sheet_name="Sheet1", index=False, header=True)


if __name__ == '__main__':
    getJavaScriptAPI(pathlib.Path.cwd() / "data/Index.txt", "./data/JavaScriptAPI.xlsx")
