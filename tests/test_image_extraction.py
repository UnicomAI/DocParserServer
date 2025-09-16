import os
import re

def fulfill_image_title(md_content, n = 3):
    # 将 Markdown 内容按行分割
    lines = md_content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        # 检查是否是图片链接
        match = re.match(r'!\[\]\((.*?)\)', line)
        if match:
            image_link = match.group(1)
            description = f"image"
            # 查看接下来的 N 行
            for j in range(1, n + 1):
                if i + j < len(lines):
                    next_line = lines[i + j].strip().lower()
                    if next_line.startswith('图') or next_line.startswith('figure'):
                        description = lines[i + j].strip()
                        break
            line = f'![{description}]({image_link})'
        new_lines.append(line)
        i += 1
    processed_md_content = '\n'.join(new_lines)
    return processed_md_content

def extract_images_from_md(md_content, parse_dir):
    # 提取图片
    if not os.path.exists(parse_dir):
        return md_content

    md_content = fulfill_image_title(md_content)
    # 提取所有图片链接
    image_links = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
    # md_content = re.sub(r'!\[Figure\]\(figures/', '![image](figures/', md_content)
    for image_link in image_links:
        if image_link.startswith("images/"):
            image_path = os.path.join(parse_dir, image_link)
            if os.path.exists(image_path):
                # 上传图片到 OSS
                # ak = "<your-token>"
                download_link = "new_link" # upload_to_oss(image_path, "doc-rag-public", "<your-api-key>")
                if download_link:
                    # 替换 Markdown 中的图片链接为 OSS 链接
                    md_content = md_content.replace(image_link, download_link)
                else:
                    print(f"Failed to upload image: {image_path}")
            else:
                print(f"Image file not found: {image_path}")
    print(f"md_content: {md_content}")
    return md_content

md_file_path = r"D:\文件\文档解析\sf\sf_mineru_aipc\auto\4-手册-AIPC 21 空调_1.md"
md_content = open(md_file_path, "r", encoding="utf-8").read()
extract_images_from_md(md_content,r"D:\文件\文档解析\sf\sf_mineru_aipc\auto")