var NISLFuzzingFunc = function (a) {
    var b = function (b, c) {
        return c == null ? !0 : a(b, c);
    };
    return b.getMessage = function () {
        return ' is optional, or it' + a.getMessage();
    }, b;
}
;
var NISLParameter0 = function(db, next) {
    let vc = require('@commons/util/mongoose-utils');
    next();
}
;
var NISLCallingResult = NISLFuzzingFunc(NISLParameter0);
print(NISLCallingResult);