"""
杯数看板数据更新脚本
用法: python convert.py <CSV文件路径> [--output data.json]
将每日CSV数据合并到 data.json，每天更新后 git push 即可自动刷新看板。
"""

import json
import os
import sys
from datetime import datetime


def parse_csv(filepath):
    """解析CSV文件，返回 (actualDaily, productDaily, dateSet)"""
    actual_daily = {}
    product_daily = {}
    date_set = set()

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print('错误: CSV文件为空')
        return None, None, None

    start_idx = 0
    first_line = lines[0].lower()
    if any(kw in first_line for kw in ['日期', '门店', 'date']):
        start_idx = 1

    sample_cols = lines[start_idx].split(',')
    has_product = len(sample_cols) >= 9

    count = 0
    prod_count = 0

    for i in range(start_idx, len(lines)):
        cols = [c.strip() for c in lines[i].split(',')]
        if len(cols) < 3:
            continue

        dv = cols[0]
        sc = cols[1]
        try:
            t = int(cols[2])
        except (ValueError, IndexError):
            continue

        if not dv or not sc:
            continue

        # 统一日期格式
        dv = dv.replace('-', '')
        if len(dv) == 8 and dv.startswith('2025'):
            dv = '2026' + dv[4:]

        if not dv.startswith('202606'):
            print(f'  跳过非6月数据: {dv}')
            continue

        if dv not in actual_daily:
            actual_daily[dv] = {}
        actual_daily[dv][sc] = t
        count += 1
        date_set.add(dv)

        # 产品数据 (9列格式)
        if has_product and len(cols) >= 9:
            try:
                iced_tea = int(cols[3]) if len(cols) > 3 else 0
                coffee = int(cols[4]) if len(cols) > 4 else 0
                can = int(cols[5]) if len(cols) > 5 else 0
                iced_tea_taste = int(cols[6]) if len(cols) > 6 else 0
                coffee_taste = int(cols[7]) if len(cols) > 7 else 0
                can_taste = int(cols[8]) if len(cols) > 8 else 0
            except (ValueError, IndexError):
                continue

            if dv not in product_daily:
                product_daily[dv] = {}
            product_daily[dv][sc] = {
                'icedTea': iced_tea,
                'coffee': coffee,
                'can': can,
                'icedTeaTaste': iced_tea_taste,
                'coffeeTaste': coffee_taste,
                'canTaste': can_taste
            }
            prod_count += 1

    msg = f'解析完成: {count}条杯数数据'
    if has_product and prod_count > 0:
        msg += f', {prod_count}条产品数据'
    msg += f', 覆盖{len(date_set)}天 ({sorted(date_set)})'
    print(msg)

    return actual_daily, product_daily, date_set


def load_existing(json_path):
    """加载已有的 data.json"""
    if not os.path.exists(json_path):
        return {'lastUpdated': '', 'viewDate': '', 'actualDaily': {}, 'productDaily': {}}

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_data(existing, new_actual, new_product):
    """合并新数据到已有数据（新数据覆盖同日期同门店）"""
    merged = {
        'lastUpdated': datetime.now().isoformat(),
        'viewDate': existing.get('viewDate', ''),
        'actualDaily': existing.get('actualDaily', {}).copy(),
        'productDaily': existing.get('productDaily', {}).copy()
    }

    # 合并杯数数据
    for date_key, stores in new_actual.items():
        if date_key not in merged['actualDaily']:
            merged['actualDaily'][date_key] = {}
        merged['actualDaily'][date_key].update(stores)

    # 合并产品数据
    for date_key, stores in new_product.items():
        if date_key not in merged['productDaily']:
            merged['productDaily'][date_key] = {}
        merged['productDaily'][date_key].update(stores)

    return merged


def main():
    if len(sys.argv) < 2:
        print('用法: python convert.py <CSV文件路径> [--output data.json]')
        print('示例: python convert.py 6月10日数据.csv')
        print('      python convert.py 6月10日数据.csv --output ../data.json')
        sys.exit(1)

    csv_path = sys.argv[1]
    output_path = 'data.json'

    # 解析 --output 参数
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            break

    if not os.path.exists(csv_path):
        print(f'错误: 找不到文件 "{csv_path}"')
        sys.exit(1)

    print(f'读取CSV: {csv_path}')
    new_actual, new_product, date_set = parse_csv(csv_path)
    if new_actual is None:
        sys.exit(1)

    print(f'加载数据文件: {output_path}')
    existing = load_existing(output_path)

    print('合并数据...')
    merged = merge_data(existing, new_actual, new_product)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f'完成! 已写入 {output_path}')

    # 统计
    total_days = len(merged['actualDaily'])
    total_records = sum(len(v) for v in merged['actualDaily'].values())
    print(f'当前共 {total_days} 天数据, {total_records} 条记录')

    if date_set:
        # 自动设置 viewDate 为最新日期
        max_date = max(date_set)
        # 如果之前没有viewDate，自动设最新
        merged['viewDate'] = max_date
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f'自动设置查看日期: {max_date}')


if __name__ == '__main__':
    main()
