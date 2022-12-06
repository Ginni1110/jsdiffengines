## 误报产生的原因

| 序号 | 引擎   | 关键字 | 问题               | 解决方案                                         |
| ---- | ------ | ------ | ------------------ | ------------------------------------------------ |
| 1    | Hermes | let    | 导致大量重复的误报 | 使用变量名替换，再去除完全重复可以解决一部分重复 |
|      |        |        |                    |                                                  |
|      |        |        |                    |                                                  |



### 1、mujs的warning会导致误报（未解决）
> mujs 会报警告，警告会导致测试结果的误报
>
> 例如：/tmp/javascriptTestcase_hhgxnhet.js:3: warning: function statements are not standard
>

**测试用例**

```js
var NISLFuzzingFunc = function () {
    for (var INDEX = 0; INDEX < 1000; INDEX++) {
        function p() {
        }
    }
};
```



### 2、分析测试结果分析方法

​		按文件的创建时间进行分析，在服务器上先打包，再下载，这样原文件的创建时间不会被修改。若单个文件下载，则创建时间都为当前时间。

