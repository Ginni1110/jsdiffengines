## Docker使用教程

### 1. 安装Docker

#### 1.1  安装Docker软件

【提示】：实验室服务器都已经安装并配置好了，无需执行，跳过1.1节。

```shell
# 安装docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
```

更多可参考[Ubuntu Docker 安装](https://www.runoob.com/docker/ubuntu-docker-install.html)



非管理员用户使用docker需要给docker分配sudo权限：

https://www.jianshu.com/p/1354e0506753

【重要提示】：如果配置需要在使用docker的时候添加sudo

#### 1.2  下载镜像

```shell
# 从远程仓库中拉取ubuntu:18.04镜像
docker pull ubuntu:18.04
```

#### 1.3  创建docker容器

基础操作：

```bash
# -i: 以交互模式运行容器
# -t: 为容器重新分配一个伪输入终端，通常与 -i 同时使用
# -d: 后台运行容器，并返回容器ID
# --name 创建容器时指定容器的名字，容器名可以自己任意去。建议：以自己的姓名命名
docker run -itd --name 容器名 ubuntu:18.04 /bin/bash
```

可选参数：

```bash
# -v: 表示需要将本地哪个目录挂载到容器中，可用于容器与宿主机之间进行共享文件夹
docker run -itd -v </Host/path/:/container/path/> ubuntu:18.04 /bin/bash

# 端口映射，将容器的端口22映射到宿主机的2048端口，端口22可以用于远程ssh登录
docker run -itd -p 2048:22 ubuntu:18.04 /bin/bash
```

#### 1.4 进入容器

```bash
# 进入容器类似于进入了虚拟机
docker exec -it <容器名或容器ID> /bin/bash
```

查看容器名或容器ID的指令：[查看容器](#3.1 查看容器)

### 2. docker容器配置

​		本节属于可选操作。先进入容器，并对容器（类似于虚拟机）进行配置。

 【重要提示】：需要先进入容器

#### 2.1 安装vim

```bash
apt-get update
apt-get install vim
```

```shell
# 异常信息：
Get:1 http://security.ubuntu.com/ubuntu bionic-security InRelease [88.7 kB]
Get:3 http://archive.ubuntu.com/ubuntu bionic-updates InRelease [88.7 kB]
Err:1 http://security.ubuntu.com/ubuntu bionic-security InRelease   
  Couldn't create temporary file /tmp/apt.conf.poD1m4 for passing config to apt-key
Err:3 http://archive.ubuntu.com/ubuntu bionic-updates InRelease
  Couldn't create temporary file /tmp/apt.conf.xYUS6c for passing config to apt-key
Get:4 http://archive.ubuntu.com/ubuntu bionic-backports InRelease [74.6 kB]
Err:4 http://archive.ubuntu.com/ubuntu bionic-backports InRelease
  Couldn't create temporary file /tmp/apt.conf.O4QjtM for passing config to apt-key
Get:2 http://archive.ubuntu.com/ubuntu bionic InRelease [242 kB]
Err:2 http://archive.ubuntu.com/ubuntu bionic InRelease                                                                       
  Couldn't create temporary file /tmp/apt.conf.H7xfAb for passing config to apt-key
```

安装vim时，若出现上述异常信息，则修改`/tmp`文件夹的权限。

```shell
chmod 1777 /tmp
```

#### 2.2 更换安装源

​		官方的安装源下载软件的速度太慢，使用国内的安装源可以加快软件的安装速度。

##### 2.2.1 备份源列表

```shell
# 备份源列表
cp /etc/apt/sources.list /etc/apt/sources.list.bak
```

##### 2.2.2 修改源列表

```shell
# 清空/etc/apt/sources.list
echo > /etc/apt/sources.list

# 将中科大或阿里云的安装源复制到sources.list文件中
vim /etc/apt/sources.list
```



**中科大安装源**

```shell
deb https://mirrors.ustc.edu.cn/ubuntu/ bionic main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-updates main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-updates main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-backports main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-backports main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-security main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-security main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-proposed main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-proposed main restricted universe multiverse
```

**阿里云安装源**

```shell
deb http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
deb-src http://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
```

### 3. Docker容器维护

#### 3.1 查看容器

```bash
# 查看所有运行的容器
docker ps

# 查看所有容器，包括暂停运行的容器
docker ps -a
```

#### 3.2 容器启动与重启

```bash
# 重启运行的容器  
docker restart <容器名或容器ID>

# 启动停止的容器
docker start <容器名或容器ID>
```

#### 3.3 容器导出与导入

```bash
# 查询需要导出容器的ID
docker ps

# 将容器ID为<容器ID>的容器导出到指定文件<文件名.tar>
docker export <容器ID> > <文件名.tar>

# 如果需要进行文件传输，最好使用zip或tar命令进行文件压缩，传输后再进行解压

# 将文件导入为docker镜像，<仓库名>和<版本号>自己设置
cat <文件名.tar> | docker import - <仓库名>:<版本号>
```

#### 3.4 容器存储为镜像

```bash
docker commit <容器 ID> <仓库名称>:<版本号>
```



### 4. 学习资料

#### 4.1 [dockerInfo](http://www.dockerinfo.net/document)





### 5. AE案例

[COMFORT](https://github.com/NWU-NISL-Fuzzing/COMFORT/tree/main/artifact_evaluation/)

[PUMPKIN Pi](https://github.com/uwplse/pumpkin-pi/tree/v2.0.0)

