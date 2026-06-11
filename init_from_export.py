"""
从原版看板导出的JSON初始化 data.json
用法: python init_from_export.py <导出文件.json> [--output data.json]

在原版看板中点击「导出」按钮，将下载的JSON文件用此脚本转为data.json格式。
"""

import json
import sys
import os
from datetime import datetime


def main():
    if len(sys.argv) < 2:
        print('用法: python init_from_export.py <导出文件.json> [--output data.json]')
        print('步骤:')
        print('  1. 打开桌面上的 6月杯数看板.html')
        print('  2. 点击右上角「导出」按钮')
        print('  3. 将下载的JSON文件路径作为参数运行此脚本')
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = 'data.json'

    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            break

    if not os.path.exists(input_path):
        print(f'错误: 找不到文件 "{input_path}"')
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)

    data = {
        'lastUpdated': datetime.now().isoformat(),
        'viewDate': '',
        'actualDaily': export_data.get('actualDaily', {}),
        'productDaily': export_data.get('productDaily', {})
    }

    actual_days = len(data['actualDaily'])
    actual_records = sum(len(v) for v in data['actualDaily'].values())
    product_days = len(data['productDaily'])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'完成! 已写入 {output_path}')
    print(f'杯数数据: {actual_days}天, {actual_records}条记录')
    if product_days > 0:
        product_records = sum(len(v) for v in data['productDaily'].values())
        print(f'产品数据: {product_days}天, {product_records}条记录')
    print(f'\n现在可以 git add data.json && git commit -m "初始化数据" && git push')


if __name__ == '__main__':
    main()
