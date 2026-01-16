import os
import json
import glob


def meger_json_structure(folder_path: str,
                         file_basename: str):
    json_pattern = os.path.join(folder_path, f"{file_basename}_*.json")
    json_files = glob.glob(json_pattern)
    if not json_files:
        print(f"没有找到与{file_basename}对应的JSON文件")
        return []

    def get_page_number(json_file):
        file_name = os.path.basename(json_file)
        parts = file_name.split('_')
        for part in reversed(parts):
            num_part = ''.join([c for c in part if c.isdigit()])
            if num_part:
                return int(num_part)
        return 0

    json_files.sort(key=get_page_number)
    print(f"找到{len(json_files)}个JSON文件，按页码排序：")
    for json_file in json_files:
        print(f"  - {os.path.basename(json_file)}")

    all_blocks = []  # 存储所有块内容
    id_counter = 0
    block_order_counter = 1

    # 收集所有块内容并同时聚合ID信息
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'parsing_res_list' in data:
                page_num = get_page_number(json_file) + 1
                for block in data['parsing_res_list']:
                    # 复制块内容并添加页码信息
                    copied_block = block.copy()
                    copied_block['block_page_no'] = page_num
                    # 聚合ID信息
                    copied_block['block_id'] = id_counter
                    copied_block['group_id'] = id_counter
                    if copied_block.get('block_order') is not None:
                        copied_block['block_order'] = block_order_counter
                        block_order_counter += 1
                    if 'image' in (copied_block.get('block_label') or ''):
                        bbox = copied_block.get('block_bbox')
                        if bbox and len(bbox) == 4:
                            bbox_str = f"{int(bbox[0])}_{int(bbox[1])}_{int(bbox[2])}_{int(bbox[3])}"
                            block_type = copied_block.get('block_label', '')
                            if 'header_image' in block_type:
                                img_path = f"img_in_header_image_box_{bbox_str}.jpg"
                            elif 'footer_image' in block_type:
                                img_path = f"img_in_footer_image_box_{bbox_str}.jpg"
                            elif 'chart' in block_type:
                                img_path = f"img_in_chart_box_{bbox_str}.jpg"
                            else:  # 默认为普通 image
                                img_path = f"img_in_image_box_{bbox_str}.jpg"

                            copied_block['block_content'] = img_path
                    id_counter += 1
                    all_blocks.append(copied_block)
        except Exception as e:
            print(f"读取文件{os.path.basename(json_file)}时出错：{e}")

    return all_blocks