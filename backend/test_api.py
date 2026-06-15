"""测试 API 接口"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    """测试所有 API 接口"""
    print("测试 API 接口...\n")

    # 1. 测试市场概览
    print("1. 测试 /api/market/overview")
    try:
        resp = requests.get(f"{BASE_URL}/api/market/overview")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   数据源: {data.get('source')}")
        print(f"   指数数量: {len(data.get('data', {}).get('indices', []))}")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 2. 测试板块排行
    print("2. 测试 /api/sectors/rank")
    try:
        resp = requests.get(f"{BASE_URL}/api/sectors/rank")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   板块数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 3. 测试强势股票
    print("3. 测试 /api/stocks/strong")
    try:
        resp = requests.get(f"{BASE_URL}/api/stocks/strong")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   股票数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 4. 测试风险股票
    print("4. 测试 /api/stocks/risk")
    try:
        resp = requests.get(f"{BASE_URL}/api/stocks/risk")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   风险股票数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 5. 测试每日报告
    print("5. 测试 /api/reports/daily")
    try:
        resp = requests.get(f"{BASE_URL}/api/reports/daily")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   报告摘要: {data.get('data', {}).get('summary', '')[:50]}...")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 6. 测试定时任务状态
    print("6. 测试 /api/scheduler/status")
    try:
        resp = requests.get(f"{BASE_URL}/api/scheduler/status")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   调度器运行: {data.get('running')}")
        print(f"   任务数量: {len(data.get('jobs', []))}")
    except Exception as e:
        print(f"   错误: {e}")

    print()

    # 7. 测试手动刷新
    print("7. 测试 POST /api/jobs/refresh")
    try:
        resp = requests.post(f"{BASE_URL}/api/jobs/refresh")
        data = resp.json()
        print(f"   状态码: {resp.status_code}")
        print(f"   状态: {data.get('data', {}).get('status')}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\nAPI 测试完成!")


if __name__ == "__main__":
    test_api()
