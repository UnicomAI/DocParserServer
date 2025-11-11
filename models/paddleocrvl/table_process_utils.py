from bs4 import BeautifulSoup, Tag
import html_text

def remove_styles_from_table(table):
    attrs_to_remove = ['style']
    # 首先处理 <table> 标签本身的样式属性
    for attr in attrs_to_remove:
        if attr in table.attrs:
            del table[attr]
    """移除表格及其子元素中的样式属性"""
    for tag in table.find_all(True):  # 查找所有标签
        if isinstance(tag, Tag):
            if tag.name not in ['td']:
                # tag.unwrap()  # 移除非必要的标签，但保留其内容
                continue

            # 移除其他样式相关属性（根据需要添加）
            for attr in attrs_to_remove:
                if attr in tag.attrs:
                    del tag[attr]
    return table

'''
    处理模型识别到的html格式表示的表格信息，移除冗余字段，不影响表格结构，减少文本长度
'''
def extract_text_with_tables(html_content):
    # 解析 HTML 内容
    soup = BeautifulSoup(html_content, 'html.parser')

    # 存储表格及其位置
    tables = []
    for idx, table in enumerate(soup.find_all('table')):
        # 创建一个唯一的占位符
        placeholder = f"[TABLE_{idx}]"
        tables.append((placeholder, str(remove_styles_from_table(table))))
        # tables.append((placeholder, str(table)))
        table.replace_with(BeautifulSoup(placeholder, 'html.parser'))

    # 提取带格式的文本
    formatted_text = html_text.extract_text(str(soup))

    # 将占位符替换回原始表格 HTML
    for placeholder, table_html in tables:
        formatted_text = formatted_text.replace(placeholder, table_html)

    return formatted_text