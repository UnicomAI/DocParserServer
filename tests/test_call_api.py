import requests

def test_model_parser_file():
    # windows
    # file_path = r'D:\文件\中船\公式计算\钢质海船入级规范2023_P658.pdf'
    # linux
    file_path = r'/home/jovyan/lzy/zc2023_P658.pdf'
    file_name = 'zc2023_P658.pdf'
    MODEL_PARSER_URL = 'http://192.168.0.229:8083/rag/model_parser_file'

    files = {
        'file': (file_name, open(file_path, 'rb'), 'application/pdf')
    }

    data = {
        'file_name': file_name,
        'extract_image': 1  # 假设这是你要发送的另一个参数
    }

    try:
        response = requests.post(MODEL_PARSER_URL, files=files, data=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    test_model_parser_file()
