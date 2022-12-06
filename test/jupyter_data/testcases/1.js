var NISLFuzzingFunc = function () {
    var arr2 = [1];
    arr2[500000] = 'X';
    return arr2;
};
NISLFuzzingFunc();