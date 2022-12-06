import pathlib


def init_data(simples_dir: str, suffix: str = "*.js") -> list:
    """
    读取目录下的所有文件内容，每一个文件的内容为数组中的一个元素
    :param simples_dir:
    :param suffix:
    :return:
    """
    path = pathlib.Path(simples_dir)
    content_list = []
    for file in path.rglob(suffix):
        content_list.append(file.read_text())
    return content_list
