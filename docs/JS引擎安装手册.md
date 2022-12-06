## JavaScript引擎安装手册

**Important Tips:**

Most JavaScript engines can be installed with [jsvu](https://github.com/GoogleChromeLabs/jsvu).

### 1. v8

```shell
#!/bin/bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$(pwd)/depot_tools:$PATH"
fetch v8
cd v8
git checkout lkgr
gclient sync

# build Debug mode
gn gen out.gn/debug --args='is_debug=true'  #  build it as a debug version
ninja -C out.gn/debug

# build Release mode
gn gen out.gn/release --args='is_debug=false'  #  build it as a release mode
ninja -C out.gn/release
```



### 2. javascriptCore

#### 2.1 Install dependencies:

\######centOS 7

[referency](https://pkgs.org/download/libicu-devel)

```
# install libicu-devel
wget http://rpms.remirepo.net/enterprise/7/remi/x86_64//libicu62-62.1-3.el7.remi.x86_64.rpm
sudo rpm -Uvh libicu62-62.1-3.el7.remi.x86_64.rpm
wget http://rpms.remirepo.net/enterprise/7/remi/x86_64//libicu62-devel-62.1-3.el7.remi.x86_64.rpm
sudo rpm -Uvh libicu62-devel-62.1-3.el7.remi.x86_64.rpm
sudo yum install python ruby bison flex cmake build-essential ninja-build git gperf
```

\#####ubuntu-18.04:

```
sudo apt-get install libicu-dev python ruby bison flex cmake build-essential ninja-build git gperf
```

#### 2.2 Download source code

```
git clone git://git.webkit.org/WebKit.git
```

#### 2.3 Build JSC shell

```
Tools/Scripts/build-webkit --jsc-only -j  # '-j' parameter accelerate compile
```

build enable debug:

```
Tools/Scripts/build-webkit --debug --jsc-only -j  # '-j' parameter accelerate compile
```

#### 2.4 Run jsc

```
./WebKitBuild/Release/bin/jsc
```

------

#### warning

if the error happened, maybe you should install a newer gcc with `sudo` .

```
-- The CMake build type is: Release
CMake Error at CMakeLists.txt:64 (message):
  GCC 6.0.0 is required to build WebKitGTK+, use a newer GCC version or clang
```

### 3. chakraCore

#### 3.1 Get binary

**Download**

https://github.com/Microsoft/ChakraCore/releases

**For Linux/OSX binaries, run the command in terminal to download the latest ChakraCore release package hosted on Azure.**

Tips: Optional

```shell
curl -SL https://aka.ms/chakracore/install | bash
```

#### 3.2 Building with source code

[Official tutorial](https://github.com/Microsoft/ChakraCore/wiki/Building-ChakraCore)



### 4. spiderMonkey

#### 4.1 New Versions

The latest javascriptCore source code can be downloaded from [GitHub](https://github.com/mozilla/gecko-dev).

#### 4.2 Old Version 

[referency](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey)

**1 Download source code, or install other version see here.**

```
mkdir mozilla
cd mozilla
wget http://ftp.mozilla.org/pub/spidermonkey/prereleases/52/pre1/
tar xvf mozjs-52.9.1pre1.tar.bz2
```

**2. Before you begin, make sure you have the right build tools for your computer. [reference](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/Build_Documentation)**

```
wget -O bootstrap.py https://hg.mozilla.org/mozilla-central/raw-file/default/python/mozboot/bin/bootstrap.py && python bootstrap.py
```

if you build JavaScript-C69.0a1, please execute follow command to install cargo.

```
# install cargo
curl https://sh.rustup.rs -sSf | sh  # then select '1' to install by default.
source $HOME/.cargo/env  # maybe you can configure your current shell run source $HOME/.cargo/env
```

install `clang+llvm-8.0.0` on ubuntu16.04. Other system see [here](http://releases.llvm.org/download.html).

```
# install llvm-8.0.0 on ubuntu 16.04
wget http://releases.llvm.org/8.0.0/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar.xz
xd -d clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar.xz
tar xvf clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar
# maybe you should run "mkdir $HOME/.local"
mv clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04 $HOME/.local
export PATH="$HOME/.local/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04/bin:$PATH"
```

install install `clang+llvm-8.0.0` on centOS. Other system see [here](http://releases.llvm.org/download.html).

```
待续

cmake -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_INSTALL_PREFIX=$HOME/.local/clang+llvm-8.0.0 -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="AArch64" -G "Unix Makefiles" ../llvm
export PATH="$HOME/.local/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04/bin:$PATH"
```

**3. Build**

```
cd mozjs-52.9.1pre1/js/src
autoconf-2.13
# ubuntu may be you can try `autoconf2.13`
# This name should end with "_OPT.OBJ" to make the version control system ignore it.
mkdir build_OPT.OBJ
cd build_OPT.OBJ
../configure
# ../configure --prefix=~/.local/spiderMonkey-60.1.1pre3  # if build spiderMonkey-60.1.1pre3 with this command, it will throw a unknown error of source code.
# Use "mozmake" on Windows
make -j
```

note: scc-titan.lancs.ac.uk, error: cannot find g++ /usr/bin/g++. Try the follow:

```
export PATH=/usr/bin:$PATH
export PATH=/usr/local/bin:$PATH
```

**4. Run spiderMonkey. More to see [A](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/Introduction_to_the_JavaScript_shell) or [B](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/Shell_global_objects).**

```
./dist/bin/js
print('hello world!')
```



### 5. rhino

#### 5.1 Download jar package

For example:

``` shell
wget https://github.com/mozilla/rhino/releases/download/Rhino1_7_13_Release/rhino-1.7.13.jar
```



#### 5.2 Building with source code

**1. install dependency**

```
sudo apt-get install openjdk-8-jdk
```

**2. Download source code of rhino1.7.9, or download on [GitHub](https://github.com/mozilla/rhino), or [mozilla](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/Rhino/Download_Rhino)**

```
wget https://github.com/mozilla/rhino/releases/download/Rhino1_7_9_Release/rhino-1.7.9.zip
```

**3. Build rhino and run all the tests.You can also see [here](https://github.com/mozilla/rhino).**

```
unzip rhino-1.7.9.zip
cd rhino1.7.9
./gradlew jar
./gradlew test
```

**4. Run rhino shell, or see [here](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/Rhino/Shell).**

```
cd /buildGradle/classes/java/main
java org.mozilla.javascript.tools.shell.Main
```

or [here](https://github.com/mozilla/rhino#running).

```
java -jar buildGradle/libs/rhino1.7
```

### 6. hermes

[Official tutorial](https://github.com/facebook/hermes/blob/master/doc/BuildingAndRunning.md)

### 7. JerryScript

[Official tutorial](https://github.com/jerryscript-project/jerryscript/blob/master/docs/00.GETTING-STARTED.md)

**Install dependencies**

```
sudo apt-get install gcc gcc-arm-none-eabi cmake cppcheck vera++ python awk bc find sed
```

**Build JerryScript** 

```shell
#------------------------------------
# 2022-12-6 更新by zjy
# 修改了cmake版本 3.22.0
# 编译命令：python tools/build.py --debug --lto=off
# 下面的命令我编译不出来 上面的可以

# --debug以debug模式编译jerryscript；若以release模式编译，删除参数--debug即可
# --profile=es2015-subset 编译的jerryscript支持ES6的部分功能
# --error-messages=on 打开报错信息
# --line-info=on 异常信息显示行号
# --mem-heap=1572864 设置运行内存的大小为1.5G,这里必须配合--cpointer-32bit=on使用。

# 简单版本
python2 tools/build.py --clean --debug --logging=on --line-info=on --error-messages=on --cpointer-32bit=on --mem-heap=1572864 --profile=es2015-subset

# 复杂版本，引擎崩溃时会打印堆栈信息
python ./tools/build.py --clean --debug --compile-flag=-fsanitize=address --compile-flag=-m32 --compile-flag=-fno-omit-frame-pointer --compile-flag=-fno-common --compile-flag=-g --strip=off --system-allocator=on --logging=on --linker-flag=-fuse-ld=gold --error-messages=on --profile=es2015-subset --line-info=on --cpointer-32bit=on --mem-heap=1572864
```

### 8. QuickJS

Download source code from [official website](https://bellard.org/quickjs/)

```shell
cd quickjs
# build QuickJS
make
```



### 9. nashorn

Download JDK from here:

https://www.oracle.com/java/technologies/javase-downloads.html



### 10. graaljs

Download graaljs from here：

https://github.com/oracle/graaljs/releases



### 11. Duktape

[Official tutorial](https://duktape.org/)

wget https://duktape.org/duktape-2.7.0.tar.xz
tar -xf duktape-2.7.0.tar.xz 
cd duktape-2.7.0
make -f Makefile.cmdline

### 12. XS

[Official website](https://github.com/Moddable-OpenSource/moddable)

**Install dependencies:**

[Official tutorial](https://github.com/Moddable-OpenSource/moddable/blob/public/documentation/Moddable%20SDK%20-%20Getting%20Started.md#linux)

```shell
sudo apt-get install gcc git wget make libncurses-dev flex bison gperf libgtk-3-dev
```

**buid xst**

```shell
git clone https://github.com/Moddable-OpenSource/moddable.git
MODDABLE="$(pwd)/moddable"
export MODDABLE
cd $MODDABLE/xs/makefiles/lin
make
```

**教程byzjy**
```shell
1.安装或更新编译所需的包：
  sudo apt-get install gcc git wget make libncurses-dev flex bison gperf

2.安装 GTK+ 3 库的开发版本：
  sudo apt-get install libgtk-3-dev

3.Projects在您的主目录中~/Projects为 Moddable SDK 存储库创建一个目录。（可以不是~/Projects，自行制定）
  cd ~/Projects
  git clone https://github.com/Moddable-OpenSource/moddable

4.在文件中设置MODDABLE环境变量~/.bashrc以指向本地 Moddable SDK 存储库目录：
  MODDABLE=~/Projects/moddable
  export MODDABLE
注意：在继续之前，您必须打开一个新的 shell 实例或在您的 shell 中手动运行导出语句。向您添加导出语句~/.profile不会更新活动 shell 实例中的环境变量。（可以不）

5.从命令行构建 Moddable 命令行工具、模拟器和调试器：
  cd $MODDABLE/build/makefiles/lin
  make

6.更新PATH您的环境变量~/.bashrc以包含工具目录：
  export PATH=$PATH:$MODDABLE/build/bin/lin/release
注意：在继续之前，您必须打开一个新的 shell 实例或在您的 shell 中手动运行导出语句。向您添加导出语句~/.profile不会更新活动 shell 实例中的环境变量。

7.安装桌面模拟器和xsbug调试器应用程序：
  cd $MODDABLE/build/makefiles/lin
  make install

8.install xst：
  cd $MODDABLE/xs/makefiles/lin
  make
  
```


### 13. MuJS

[Official website](https://mujs.com/)

```shell
# 下载源码并解压
wget https://mujs.com/downloads/mujs-1.3.2.tar.xz
tar -xvf mujs-1.3.2.tar.xz
cd mujs-1.3.2
# 编译安装
make
# 测试
./build/release/mujs testcase.js
```

