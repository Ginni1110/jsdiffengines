var NISLFuzzingFunc = function (id) {
    var events = [1,2,5];
    let testId;
    if (testId === id) {
        events.push({
            type: 'destroy',
            id
        });
    }
};
var NISLParameter0 = undefined;
var NISLCallingResult = NISLFuzzingFunc(NISLParameter0);
print(NISLCallingResult);