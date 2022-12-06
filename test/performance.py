import pathlib
from Harness import run_test_case

testbed = "/home/engines/XS/moddable-771d593/moddable/build/bin/lin/release/xst"
testcase = pathlib.Path("./test/data/performance.js")
result = run_test_case(testbed=testbed, testcase_path=testcase, time="36000")
print(result)