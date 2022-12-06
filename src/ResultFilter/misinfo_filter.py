# -*- coding: utf-8 -*-
#
# @Version: python 3.7
# @File: misinfo_Filting.py
# @Author: ty
# @E-mail: nwu_ty@163.com
# @Time: 2020/4/13
# @Description:
# @Input:
# @Output:
#


def filtering_rules(engine_name: str, key_exception: str) -> bool:
    flag = True
    # 过滤条件1：过滤掉hermes引擎中，关键信息只有note:xxx类的数据
    if engine_name.strip().lower() == 'hermes' and key_exception.strip().startswith('note:'):
        flag = False

    # 其他过滤条件以后逐渐完善...

    return flag


