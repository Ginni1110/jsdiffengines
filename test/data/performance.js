var NISLFuzzingFunc = function(size) {
    var array = new Array(size);
    while (size--){
        array[size] = 0;
    }
    print(array.length);
};
var NISLParameter0 = 50000;
NISLFuzzingFunc(NISLParameter0);